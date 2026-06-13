# Dockerfile pour Mosquitto avec script personnalisé
FROM eclipse-mosquitto:2.0

# Installer dos2unix pour gérer les fins de ligne Windows
USER root
RUN apk add --no-cache dos2unix

# Copier le script d'entrée personnalisé
COPY mosquitto-docker-entrypoint.sh /mosquitto-docker-entrypoint.sh

# Corriger les fins de ligne et donner les permissions d'exécution
RUN dos2unix /mosquitto-docker-entrypoint.sh && \
    chmod +x /mosquitto-docker-entrypoint.sh

# Copier la configuration TLS
COPY mosquitto-tls.conf /mosquitto/config/mosquitto.conf

# Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /mosquitto/data /mosquitto/logs /mosquitto/config && \
    chown -R mosquitto:mosquitto /mosquitto && \
    chmod -R 755 /mosquitto

# # Définir l'utilisateur par défaut
USER mosquitto

# Définir l'entrypoint
ENTRYPOINT ["/mosquitto-docker-entrypoint.sh"]
