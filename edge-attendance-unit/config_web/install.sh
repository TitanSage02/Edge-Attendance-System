#!/bin/bash

# Script d'installation pour l'interface web de configuration CREC

echo "=== Installation Interface Web Configuration CREC ==="
echo ""

# Vérifier si le script est exécuté avec les droits sudo
if [ "$EUID" -ne 0 ]; then
    echo "Ce script doit être exécuté avec sudo"
    exit 1
fi

# Répertoire de l'application
APP_DIR="/home/unit/CREC-Presence-Unit"
CONFIG_WEB_DIR="$APP_DIR/config_web"

# Vérifier que le répertoire existe
if [ ! -d "$CONFIG_WEB_DIR" ]; then
    echo "Erreur: Le répertoire $CONFIG_WEB_DIR n'existe pas"
    exit 1
fi

# Activer l'environnement virtuel si nécessaire
if [ -f "$APP_DIR/venv/bin/activate" ]; then
    echo "Activation de l'environnement virtuel..."
    source "$APP_DIR/venv/bin/activate"
else
    echo "Aucun environnement virtuel trouvé, création d'un nouvel environnement..."
    python3 -m venv "$APP_DIR/venv"
    source "$APP_DIR/venv/bin/activate"
    echo "Environnement virtuel créé et activé"
fi

echo "Installation des dépendances Python..."
pip3 install -r "$CONFIG_WEB_DIR/requirements.txt"

echo "Création du fichier .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "✓ Fichier .env créé depuis .env.example"
else
    echo "✓ Fichier .env existe déjà"
fi

echo "Configuration des permissions..."
# Donner les permissions à l'utilisateur unit pour le développement
chown -R unit:unit "$APP_DIR"
# Mais permettre à root de lire les fichiers pour le service
chmod -R o+r "$APP_DIR"
chmod +x "$APP_DIR/config_web/app.py"

echo "Installation du service systemd..."
cp "$CONFIG_WEB_DIR/crec-config-web.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable crec-config-web.service

echo "Démarrage du service..."
systemctl start crec-config-web.service

echo ""
echo "=== Installation terminée ==="
echo ""
echo "L'interface web est maintenant disponible sur:"
echo "  http://localhost"
echo "  http://$(hostname -I | awk '{print $1}')"
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl status crec-config-web    # Vérifier le statut"
echo "  sudo systemctl stop crec-config-web      # Arrêter le service"
echo "  sudo systemctl start crec-config-web     # Démarrer le service"
echo "  sudo systemctl restart crec-config-web   # Redémarrer le service"
echo "  sudo journalctl -u crec-config-web -f    # Voir les logs"
echo ""