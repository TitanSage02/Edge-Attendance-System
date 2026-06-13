#!/bin/bash

# Script d'installation pour le service Edge Attendance System Detection

echo "=== Installation Service Edge Attendance System Detection ==="
echo ""

# Vérifier si le script est exécuté avec les droits sudo
if [ "$EUID" -ne 0 ]; then
    echo "Ce script doit être exécuté avec sudo"
    exit 1
fi

# Répertoire de l'application
APP_DIR="/home/unit/CREC-Presence-Unit"

# Vérifier que le répertoire existe
if [ ! -d "$APP_DIR" ]; then
    echo "Erreur: Le répertoire $APP_DIR n'existe pas"
    exit 1
fi

# Vérifier que startup.py existe
if [ ! -f "$APP_DIR/startup.py" ]; then
    echo "Erreur: Le fichier startup.py n'existe pas dans $APP_DIR"
    exit 1
fi

# Vérifier que l'environnement virtuel existe
if [ ! -f "$APP_DIR/venv/bin/python" ]; then
    echo "Erreur: L'environnement virtuel n'existe pas dans $APP_DIR/venv"
    echo "Créez d'abord l'environnement virtuel avec: python3 -m venv venv"
    exit 1
fi

echo "Vérification des permissions..."
# S'assurer que l'utilisateur unit possède les fichiers
chown -R unit:unit "$APP_DIR"

# Rendre startup.py exécutable
chmod +x "$APP_DIR/startup.py"

echo "Installation du service systemd..."
# Copier le fichier service
cp "$APP_DIR/crec-presence.service" /etc/systemd/system/

# Recharger systemd
systemctl daemon-reload

# Activer le service pour qu'il démarre automatiquement
systemctl enable crec-presence.service

echo "Test du service..."
# Démarrer le service
systemctl start crec-presence.service

# Attendre un peu pour laisser le service démarrer
sleep 3

# Vérifier le statut
echo ""
echo "Statut du service:"
systemctl status crec-presence.service --no-pager -l

echo ""
echo "=== Installation terminée ==="
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl status crec-presence     # Vérifier le statut"
echo "  sudo systemctl stop crec-presence       # Arrêter le service"
echo "  sudo systemctl start crec-presence      # Démarrer le service"
echo "  sudo systemctl restart crec-presence    # Redémarrer le service"
echo "  sudo systemctl disable crec-presence    # Désactiver le démarrage automatique"
echo "  sudo journalctl -u crec-presence -f     # Voir les logs en temps réel"
echo "  sudo journalctl -u crec-presence -n 50  # Voir les 50 dernières lignes de logs"
echo ""
