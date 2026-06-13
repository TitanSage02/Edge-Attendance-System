#!/bin/bash

# Script de gestion du service Edge Attendance System Detection

SERVICE_NAME="crec-presence"

show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|enable|disable|install}"
    echo ""
    echo "Commandes:"
    echo "  start      Démarrer le service"
    echo "  stop       Arrêter le service"
    echo "  restart    Redémarrer le service"
    echo "  status     Afficher le statut du service"
    echo "  logs       Afficher les logs en temps réel"
    echo "  enable     Activer le démarrage automatique"
    echo "  disable    Désactiver le démarrage automatique"
    echo "  install    Installer le service (nécessite sudo)"
    echo ""
}

case "$1" in
    start)
        echo "Démarrage du service $SERVICE_NAME..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    stop)
        echo "Arrêt du service $SERVICE_NAME..."
        sudo systemctl stop $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    restart)
        echo "Redémarrage du service $SERVICE_NAME..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    status)
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    logs)
        echo "Logs en temps réel (Ctrl+C pour quitter):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo "Activation du démarrage automatique..."
        sudo systemctl enable $SERVICE_NAME
        echo "✅ Service activé pour le démarrage automatique"
        ;;
    disable)
        echo "Désactivation du démarrage automatique..."
        sudo systemctl disable $SERVICE_NAME
        echo "✅ Démarrage automatique désactivé"
        ;;
    install)
        if [ "$EUID" -ne 0 ]; then
            echo "L'installation nécessite sudo"
            echo "Utilisez: sudo $0 install"
            exit 1
        fi
        
        APP_DIR="/home/unit/CREC-Presence-Unit"
        
        if [ ! -f "$APP_DIR/crec-presence.service" ]; then
            echo "Erreur: Fichier crec-presence.service non trouvé"
            exit 1
        fi
        
        echo "Installation du service..."
        cp "$APP_DIR/crec-presence.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable $SERVICE_NAME
        echo "✅ Service installé et activé"
        ;;
    *)
        show_help
        exit 1
        ;;
esac
