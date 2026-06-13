#!/bin/bash

# =============================================================================
# Script pour configurer les certificats TLS pour MQTT
# Ce script télécharge et configure les certificats nécessaires
# =============================================================================

set -e

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
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CERTS_DIR="$BASE_DIR/certs"

# Configuration par défaut
MQTT_BROKER="${MQTT_BROKER:-api-presence.crec-sj.org}"
MQTT_TLS_PORT="${MQTT_TLS_PORT:-8883}"

log_info "=== CONFIGURATION DES CERTIFICATS TLS POUR MQTT ==="

# Créer le répertoire des certificats
mkdir -p "$CERTS_DIR"

# Fonction pour télécharger le certificat du serveur
download_server_cert() {
    log_info "Téléchargement du certificat du serveur MQTT..."
    
    # Obtenir le certificat du serveur via openssl
    if command -v openssl &> /dev/null; then
        echo | openssl s_client -servername "$MQTT_BROKER" -connect "$MQTT_BROKER:$MQTT_TLS_PORT" 2>/dev/null | \
        openssl x509 -outform PEM > "$CERTS_DIR/server.crt"
        
        if [ -f "$CERTS_DIR/server.crt" ] && [ -s "$CERTS_DIR/server.crt" ]; then
            log_info "✅ Certificat serveur téléchargé: $CERTS_DIR/server.crt"
            
            # Afficher les informations du certificat
            log_info "Informations du certificat:"
            openssl x509 -in "$CERTS_DIR/server.crt" -text -noout | grep -E "(Subject:|Issuer:|Not After :|DNS:|IP Address:)" || true
        else
            log_error "❌ Échec du téléchargement du certificat serveur"
            return 1
        fi
    else
        log_error "openssl n'est pas installé. Installation requise."
        return 1
    fi
}

# Fonction pour télécharger les certificats racine Let's Encrypt
download_letsencrypt_certs() {
    log_info "Téléchargement des certificats racine Let's Encrypt..."
    
    # URLs des certificats Let's Encrypt
    ISRG_ROOT_X1="https://letsencrypt.org/certs/isrgrootx1.pem"
    LETS_ENCRYPT_R3="https://letsencrypt.org/certs/lets-encrypt-r3.pem"
    
    if command -v curl &> /dev/null; then
        curl -s "$ISRG_ROOT_X1" -o "$CERTS_DIR/isrg-root-x1.pem"
        curl -s "$LETS_ENCRYPT_R3" -o "$CERTS_DIR/lets-encrypt-r3.pem"
        
        # Créer un bundle avec tous les certificats CA
        cat "$CERTS_DIR/isrg-root-x1.pem" "$CERTS_DIR/lets-encrypt-r3.pem" > "$CERTS_DIR/ca-bundle.pem"
        
        log_info "✅ Certificats Let's Encrypt téléchargés"
    elif command -v wget &> /dev/null; then
        wget -q "$ISRG_ROOT_X1" -O "$CERTS_DIR/isrg-root-x1.pem"
        wget -q "$LETS_ENCRYPT_R3" -O "$CERTS_DIR/lets-encrypt-r3.pem"
        
        # Créer un bundle avec tous les certificats CA
        cat "$CERTS_DIR/isrg-root-x1.pem" "$CERTS_DIR/lets-encrypt-r3.pem" > "$CERTS_DIR/ca-bundle.pem"
        
        log_info "✅ Certificats Let's Encrypt téléchargés"
    else
        log_warn "Ni curl ni wget disponible. Utilisation des certificats système."
        return 1
    fi
}

# Fonction pour tester la connexion TLS
test_tls_connection() {
    log_info "Test de la connexion TLS vers $MQTT_BROKER:$MQTT_TLS_PORT..."
    
    if command -v openssl &> /dev/null; then
        if echo | openssl s_client -connect "$MQTT_BROKER:$MQTT_TLS_PORT" -servername "$MQTT_BROKER" 2>/dev/null | grep -q "Verify return code: 0"; then
            log_info "✅ Connexion TLS réussie"
            return 0
        else
            log_warn "⚠️  Connexion TLS avec erreur de vérification"
            return 1
        fi
    else
        log_warn "openssl non disponible pour le test"
        return 1
    fi
}

# Fonction pour mettre à jour le fichier .env
update_env_file() {
    log_info "Mise à jour du fichier .env..."
    
    ENV_FILE="$BASE_DIR/.env"
    
    # Créer .env à partir de .env.example si nécessaire
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$BASE_DIR/.env.example" ]; then
            cp "$BASE_DIR/.env.example" "$ENV_FILE"
            log_info "Fichier .env créé à partir de .env.example"
        else
            log_error "Aucun fichier .env.example trouvé"
            return 1
        fi
    fi
    
    # Mise à jour des paramètres TLS dans .env
    sed -i.bak \
        -e "s|^MQTT_BROKER=.*|MQTT_BROKER='$MQTT_BROKER'|" \
        -e "s|^USE_TLS=.*|USE_TLS=true|" \
        -e "s|^MQTT_TLS_PORT=.*|MQTT_TLS_PORT=$MQTT_TLS_PORT|" \
        "$ENV_FILE"
    
    # Ajouter le chemin du certificat CA si un bundle a été créé
    if [ -f "$CERTS_DIR/ca-bundle.pem" ]; then
        if ! grep -q "MQTT_CA_CERT=" "$ENV_FILE"; then
            echo "MQTT_CA_CERT='$CERTS_DIR/ca-bundle.pem'" >> "$ENV_FILE"
        else
            sed -i.bak "s|^#*MQTT_CA_CERT=.*|MQTT_CA_CERT='$CERTS_DIR/ca-bundle.pem'|" "$ENV_FILE"
        fi
    fi
    
    log_info "✅ Fichier .env mis à jour"
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --broker HOSTNAME    Hostname du broker MQTT (défaut: api-presence.crec-sj.org)"
    echo "  --port PORT         Port TLS du broker MQTT (défaut: 8883)"
    echo "  --test-only         Tester la connexion uniquement"
    echo "  --no-update-env     Ne pas mettre à jour le fichier .env"
    echo "  -h, --help          Afficher cette aide"
}

# Traitement des arguments
UPDATE_ENV=true
TEST_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --broker)
            MQTT_BROKER="$2"
            shift 2
            ;;
        --port)
            MQTT_TLS_PORT="$2"
            shift 2
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --no-update-env)
            UPDATE_ENV=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Exécution principale
log_info "Configuration TLS pour $MQTT_BROKER:$MQTT_TLS_PORT"

if [ "$TEST_ONLY" = true ]; then
    test_tls_connection
    exit $?
fi

# Télécharger les certificats
download_letsencrypt_certs || log_warn "Échec du téléchargement des certificats Let's Encrypt"
download_server_cert || log_warn "Échec du téléchargement du certificat serveur"

# Tester la connexion
test_tls_connection || log_warn "Test de connexion TLS échoué"

# Mettre à jour .env si demandé
if [ "$UPDATE_ENV" = true ]; then
    update_env_file
fi

log_info "=== CONFIGURATION TLS TERMINÉE ==="
log_info "Certificats stockés dans: $CERTS_DIR"
log_info "Pour utiliser TLS, assurez-vous que USE_TLS=true dans votre .env"

exit 0
