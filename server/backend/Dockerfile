# Utilise Python 3.10-slim comme image de base
FROM python:3.10-slim

# Installe les dépendances système nécessaires pour InsightFace et OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgdal-dev \
    ffmpeg \
    netcat-traditional \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Définit le répertoire de travail
WORKDIR /backend-crec

# Copie les fichiers de dépendances
COPY requirements.txt ./

# Met à jour pip et installe les dépendances Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code de l'application
COPY . .

# Créer un utilisateur non-root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Créer les répertoires nécessaires et assigner les permissions
RUN mkdir -p /backend-crec/data /backend-crec/logs /backend-crec/vector_db && \
    chown -R appuser:appgroup /backend-crec && \
    chmod -R 755 /backend-crec

# Corriger les permissions et les fins de ligne du script d'entrée
RUN chmod +x docker-entrypoint.sh && \
    chmod 755 docker-entrypoint.sh && \
    dos2unix docker-entrypoint.sh 2>/dev/null || true && \
    chown appuser:appgroup docker-entrypoint.sh

# Changer vers l'utilisateur non-root
USER appuser

# Expose le port 8000
EXPOSE 8000

# Utilise le script d'entrée
ENTRYPOINT ["bash", "./docker-entrypoint.sh"]

# ENTRYPOINT ["/bin/bash", "/backend-crec/docker-entrypoint.sh"]
