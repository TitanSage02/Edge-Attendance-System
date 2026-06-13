#!/bin/sh
set -e

echo "===== DÉMARRAGE DU CONTENEUR MOSQUITTO ====="

# Afficher les variables d'environnement disponibles (sans les secrets)
echo "Variables d'environnement disponibles:"
echo "MOSQUITTO_USERNAME: ${MOSQUITTO_USERNAME:-non défini}"
echo "MQTT_USER: ${MQTT_USER:-non défini}"
echo "MONITORING_USERNAME: ${MONITORING_USERNAME:-non défini}"

# Assurer que les répertoires existent avec les bonnes permissions
mkdir -p /mosquitto/config
mkdir -p /mosquitto/data
mkdir -p /mosquitto/log

chown -R mosquitto:mosquitto /mosquitto/config
chown -R mosquitto:mosquitto /mosquitto/data
chown -R mosquitto:mosquitto /mosquitto/log

chmod -R 755 /mosquitto/config
chmod -R 755 /mosquitto/data
chmod -R 755 /mosquitto/log

echo "Répertoires créés et permissions appliquées"

# Créer la configuration depuis les variables d'environnement
cat > /mosquitto/config/mosquitto.conf << EOL
# Configuration Mosquitto générée automatiquement
# Configurations des listeners
listener 1883 0.0.0.0
protocol mqtt
socket_domain ipv4
max_connections -1

listener 9001 0.0.0.0
protocol websockets
socket_domain ipv4
max_connections -1
websockets_headers_size 64000

# Paramètres généraux
per_listener_settings false
allow_anonymous false
password_file /mosquitto/config/passwd

# Persistence
persistence true
persistence_location /mosquitto/data/
persistent_client_expiration 1d
autosave_interval 300

# Logs
log_dest stdout
log_dest file /mosquitto/log/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
connection_messages true
log_timestamp true
log_timestamp_format %Y-%m-%d %H:%M:%S

# Performances
max_queued_messages 1000
max_inflight_messages 20
queue_qos0_messages false
allow_zero_length_clientid true
set_tcp_nodelay true
max_packet_size 10240

# Sécurité
allow_duplicate_messages false
max_connections 1000
max_queued_messages 1000
max_inflight_messages 20
EOL

echo "Fichier de configuration créé"

# Créer le fichier des mots de passe vide
touch /mosquitto/config/passwd
chown mosquitto:mosquitto /mosquitto/config/passwd
chmod 600 /mosquitto/config/passwd

echo "Fichier de mots de passe créé"

# Fonction pour configurer un utilisateur MQTT
configure_user() {
    local username=$1
    local password=$2
    local description=$3
    
    if [ ! -z "$username" ] && [ ! -z "$password" ]; then
        # Supprimer l'utilisateur s'il existe déjà
        if grep -q "^$username:" /mosquitto/config/passwd; then
            mosquitto_passwd -D /mosquitto/config/passwd "$username"
        fi
        # Ajouter l'utilisateur avec le nouveau mot de passe
        mosquitto_passwd -b /mosquitto/config/passwd "$username" "$password"
        echo "✅ $description ($username) configuré avec succès"
        return 0
    fi
    echo "⚠️ AVERTISSEMENT: $description non configuré (identifiants manquants)"
    return 1
}

# Configuration des utilisateurs
echo "Configuration des utilisateurs MQTT..."
users_configured=0

# Backend user (MOSQUITTO_USERNAME a la priorité sur MQTT_USER pour le backend)
if [ ! -z "$MOSQUITTO_USERNAME" ]; then
    configure_user "$MOSQUITTO_USERNAME" "$MOSQUITTO_PASSWORD" "Utilisateur backend" && users_configured=$((users_configured + 1))
fi

# Module user (toujours configurer l'utilisateur des modules)
if [ ! -z "$MQTT_USER" ]; then
    configure_user "$MQTT_USER" "$MQTT_PASSWORD" "Utilisateur modules" && users_configured=$((users_configured + 1))
fi

# Monitoring user
configure_user "$MONITORING_USERNAME" "$MONITORING_PASSWORD" "Utilisateur monitoring" && users_configured=$((users_configured + 1))

# Vérifier qu'au moins un utilisateur est configuré
if [ "$users_configured" -eq 0 ]; then
    echo "❌ ERREUR: Aucun utilisateur configuré. Au moins un utilisateur est requis."
    echo "   Configurer soit MOSQUITTO_USERNAME/MQTT_USER avec leur mot de passe"
    exit 1
fi

# Afficher les utilisateurs configurés
echo "Liste des utilisateurs configurés:"
cat /mosquitto/config/passwd | cut -d: -f1

# Exécution de Mosquitto avec la configuration générée
echo "===== DÉMARRAGE DE MOSQUITTO ====="
exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf -v
