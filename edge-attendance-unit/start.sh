#!/bin/bash

# =============================================================================
# Script de démarrage pour le module Edge Attendance System
# Ce script:
# 1. Met à jour le système
# 2. Crée un environnement virtuel Python
# 3. Installe les dépendances
# 4. Lance le module Edge Attendance System
# =============================================================================

set -e  # Arrêt du script en cas d'erreur

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages formatés
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Obtenir le répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Nom de l'environnement virtuel
VENV_DIR="$SCRIPT_DIR/venv"

# Vérifier les arguments
RUN_DIAGNOSTIC=0
SKIP_UPDATE=0
FORCE_REINSTALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --diagnostic)
            RUN_DIAGNOSTIC=1
            shift
            ;;
        --skip-update)
            SKIP_UPDATE=1
            shift
            ;;
        --force-reinstall)
            FORCE_REINSTALL=1
            shift
            ;;
        -h|--help)
            echo "Usage: ./start.sh [OPTIONS]"
            echo "Options:"
            echo "  --diagnostic        Exécuter les diagnostics"
            echo "  --skip-update       Effectuer la mise à jour du système"
            echo "  --force-reinstall   Recréer l'environnement virtuel"
            exit 0
            ;;
    esac
done

# Fonction pour la mise à jour du système
update_system() {
    if [ $SKIP_UPDATE -eq 0 ]; then
        log_warn "Mise à jour du système ignorée (--skip-update)"
        return
    fi
    
    log_info "Mise à jour du système..."
    
    # Vérifier si nous sommes root
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo &> /dev/null; then
            SUDO="sudo"
        else
            log_error "Ce script nécessite les privilèges sudo pour mettre à jour le système"
            exit 1
        fi
    else
        SUDO=""
    fi
    
    # Mise à jour selon la distribution
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu/Raspbian
        $SUDO apt-get update -y
        $SUDO apt-get upgrade -y
        $SUDO apt purge vlc vlc-bin libvlc-bin vlc-plugin-* --auto-remove
        $SUDO apt install -y libcap-dev libcamera-dev libcamera-apps python3-libcamera python3-picamera2
    fi
    
    log_info "Mise à jour du système terminée"
}

# Fonction pour installer les dépendances système
install_system_dependencies() {
    log_info "Installation des dépendances système..."
    
    # Vérifier si nous sommes root
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo &> /dev/null; then
            SUDO="sudo"
        else
            log_error "Ce script nécessite les privilèges sudo pour installer les dépendances"
            exit 1
        fi
    else
        SUDO=""
    fi
    
    # Liste des paquets nécessaires
    PACKAGES="python3 python3-pip python3-venv i2c-tools libi2c-dev"
    
    # Installation selon la distribution
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu/Raspbian
        $SUDO apt-get install -y $PACKAGES
    else
        log_warn "Système de paquets non reconnu. Les dépendances système devront être installées manuellement."
    fi
    
    log_info "Installation des dépendances système terminée"
}

# Fonction pour créer l'environnement virtuel Python
setup_virtual_env() {
    log_info "Configuration de l'environnement virtuel Python..."
    
    # Si l'environnement existe déjà
    if [ -d "$VENV_DIR" ] && [ $FORCE_REINSTALL -eq 0 ]; then
        log_warn "L'environnement virtuel existe déjà. Utilisation de l'existant."
    else
        # Supprimer l'environnement s'il existe et qu'on force la réinstallation
        if [ -d "$VENV_DIR" ]; then
            log_info "Suppression de l'ancien environnement virtuel..."
            rm -rf "$VENV_DIR"
        fi
        
        # Créer le nouvel environnement
        log_info "Création d'un nouvel environnement virtuel..."
        python3 -m venv "$VENV_DIR" --system-site-packages
    fi
    
    # Activer l'environnement virtuel
    source "$VENV_DIR/bin/activate"
    
    # Mettre à jour pip
    log_info "Mise à jour de pip..."
    pip install --upgrade pip
    
    log_info "Environnement virtuel configuré avec succès"
}

# Fonction pour installer les dépendances Python
install_python_dependencies() {
    log_info "Installation des dépendances Python..."
    
    # Vérifier si requirements.txt existe
    if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
        log_error "Fichier requirements.txt non trouvé!"
        exit 1
    fi
    
    # Installer les dépendances
    pip install -r "$SCRIPT_DIR/requirements.txt"
    # update specific packages
    pip install --upgrade  chromadb posthog

    
    log_info "Installation des dépendances Python terminée"
}

# Fonction pour configurer les certificats TLS
setup_tls_certificates() {
    log_info "Configuration des certificats TLS pour MQTT..."
    
    # Vérifier si le script de configuration TLS existe
    TLS_SCRIPT="$SCRIPT_DIR/scripts/setup_tls_certs.sh"
    if [ -f "$TLS_SCRIPT" ]; then
        chmod +x "$TLS_SCRIPT"
        
        # Lire la configuration MQTT depuis .env si disponible
        if [ -f "$SCRIPT_DIR/.env" ]; then
            source "$SCRIPT_DIR/.env" 2>/dev/null || true
        fi
        
        # Exécuter le script de configuration TLS
        if [ -n "$MQTT_BROKER" ] && [ "$USE_TLS" = "true" ]; then
            log_info "Configuration TLS pour $MQTT_BROKER..."
            bash "$TLS_SCRIPT" --broker "$MQTT_BROKER" || log_warn "Configuration TLS partiellement échouée"
        else
            log_info "TLS désactivé ou MQTT_BROKER non configuré, configuration ignorée"
        fi
    else
        log_warn "Script de configuration TLS non trouvé: $TLS_SCRIPT"
    fi
}
run_module() {
    log_info "Lancement du module Edge Attendance System..."
    
    # Copie de .env.example vers .env uniquement si .env n'existe pas
   
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    log_info "Fichier .env créé à partir de .env.example"
    log_info "⚠️  Pensez à modifier le fichier .env selon votre environnement (debug, MQTT, etc.)"
  
    # Vérifier si main.py existe
    if [ ! -f "$SCRIPT_DIR/main.py" ]; then
        log_error "Fichier main.py non trouvé!"
        exit 1
    fi
    
    # Exécuter le module
    if [ $RUN_DIAGNOSTIC -eq 1 ]; then
        # Mode diagnostic
        log_info "Exécution en mode diagnostic..."
        python "$SCRIPT_DIR/diagnostic.py" --all
    else
        # Mode normal
        # Exécuter le programme principal avec surveillance
        {
            # Activer le mode debug pour plus de logs
            python "$SCRIPT_DIR/startup.py"
            EXIT_CODE=$?
            
            if [ $EXIT_CODE -eq 139 ]; then
                log_error "Erreur de segmentation détectée (code 139)"
                log_info "Lancement du script de nettoyage d'urgence..."
                # Exécuter le script de nettoyage d'urgence
                python "$SCRIPT_DIR/cleanup.py"
            elif [ $EXIT_CODE -ne 0 ]; then
                log_error "Le programme s'est terminé avec le code d'erreur: $EXIT_CODE"
                log_info "Nettoyage des ressources..."
                python "$SCRIPT_DIR/cleanup.py"
            fi
            
            return $EXIT_CODE
        }
    fi
}

# Exécution principale
log_info "=== DÉMARRAGE DU MODULE EDGE ATTENDANCE SYSTEM ==="
log_info "Répertoire: $SCRIPT_DIR"

# Mise à jour du système
update_system

# Installation des dépendances système
install_system_dependencies

# Configuration de l'environnement virtuel
setup_virtual_env

# Installation des dépendances Python
install_python_dependencies

# Configuration des certificats TLS
setup_tls_certificates

# Exécution du module
run_module

log_info "=== FIN DU SCRIPT ==="
exit 0