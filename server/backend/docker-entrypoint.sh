#!/bin/bash
set -e

echo "🚀 Démarrage du conteneur Edge Attendance System API (VM Optimized)..."

# Variables d'environnement pour debugging
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Fonction de logging avec timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Fonction de vérification de santé
check_health() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=${4:-30}
    local attempt=1
    
    log "⏳ Attente de $service_name ($host:$port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log "✅ $service_name est prêt!"
            return 0
        fi
        
        log "Tentative $attempt/$max_attempts pour $service_name..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log "❌ Timeout en attente de $service_name"
    return 1
}

# Vérification de l'utilisateur courant
log "👤 Utilisateur courant: $(whoami)"
log "🏠 Répertoire home: $HOME"
log "📁 Répertoire de travail: $(pwd)"

# Créer les répertoires nécessaires avec les bonnes permissions
log "📁 Création des répertoires de données..."
mkdir -p /backend-crec/data /backend-crec/logs /backend-crec/vector_db || true

# Attendre que la base de données soit prête
log "⏳ Attente de la base de données..."
check_health "PostgreSQL" "db" "5432"

# Le nouveau système d'initialisation automatique se fait via l'application
log "✅ Base de données prête, l'initialisation des tables se fera automatiquement au démarrage de l'application"

# Vérifier les permissions en tant qu'utilisateur actuel
log "🔐 Vérification des permissions..."
if [ "$(whoami)" = "appuser" ]; then
    log "✅ Exécution en tant qu'utilisateur non-root"
else
    log "⚠️ Exécution en tant qu'utilisateur: $(whoami)"
fi

# Test d'écriture pour vérifier les permissions
log "🧪 Test d'écriture dans les répertoires..."
test_file="/backend-crec/logs/startup-test.log"
if echo "Test de démarrage $(date)" > "$test_file" 2>/dev/null; then
    log "✅ Écriture dans /backend-crec/logs OK"
    rm -f "$test_file"
else
    log "❌ Erreur d'écriture dans /backend-crec/logs"
    ls -la /backend-crec/
    exit 1
fi

# Affichage des informations système pour debug
log "🖥️ Informations système:"
log "  - Architecture: $(uname -m)"
log "  - Noyau: $(uname -r)"
log "  - Mémoire disponible: $(free -h | grep Mem | awk '{print $7}' || echo 'N/A')"
log "  - Espace disque: $(df -h . | tail -1 | awk '{print $4}' || echo 'N/A')"

# Vérification des dépendances Python critiques
log "🐍 Vérification des dépendances Python..."
python -c "
import sys
print(f'Python version: {sys.version}')

# Test des imports critiques
critical_imports = [
    'fastapi',
    'uvicorn', 
    'sqlalchemy',
    'asyncpg',
    'numpy',
    'cv2',  # opencv-python
]

failed_imports = []
for module in critical_imports:
    try:
        __import__(module)
        print(f'✅ {module} OK')
    except ImportError as e:
        print(f'❌ {module} FAILED: {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'Imports échoués: {failed_imports}')
    sys.exit(1)
else:
    print('✅ Tous les imports critiques réussis')
"

if [ $? -ne 0 ]; then
    log "❌ Erreur lors de la vérification des dépendances Python"
    exit 1
fi

# Test optionnel des dépendances lourdes (InsightFace)
log "🔍 Test optionnel des dépendances lourdes..."
python -c "
try:
    import insightface
    print('✅ InsightFace importé avec succès')
except ImportError as e:
    print(f'⚠️ InsightFace non disponible: {e}')
except Exception as e:
    print(f'⚠️ Erreur InsightFace: {e}')

try:
    import faiss
    print('✅ FAISS importé avec succès')
except ImportError as e:
    print(f'⚠️ FAISS non disponible: {e}')
except Exception as e:
    print(f'⚠️ Erreur FAISS: {e}')
" || log "⚠️ Certaines dépendances optionnelles ne sont pas disponibles"

# Attendre que la base de données soit prête avec retry amélioré
if ! check_health "PostgreSQL" "db" "5432" 60; then
    log "❌ PostgreSQL non accessible après 2 minutes"
    exit 1
fi

# Test de connexion à la base de données
log "🔌 Test de connexion à la base de données..."
python -c "
import asyncpg
import asyncio
import os

async def test_db():
    try:
        conn = await asyncpg.connect(
            host='db',
            port=5432,
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'crec_db')
        )
        await conn.close()
        print('✅ Connexion à la base de données réussie')
        return True
    except Exception as e:
        print(f'❌ Erreur de connexion à la base: {e}')
        return False

result = asyncio.run(test_db())
exit(0 if result else 1)
"

if [ $? -ne 0 ]; then
    log "❌ Test de connexion à la base échoué"
    exit 1
fi

# Note: La création et gestion des tables se fait automatiquement 
# au démarrage de l'application FastAPI via le système SQLAlchemy
log "🗄️ Les tables de base de données seront créées automatiquement au démarrage de l'application"

# Attendre MQTT si configuré
if [ "${MQTT_HOST}" != "" ]; then
    check_health "MQTT Mosquitto" "${MQTT_HOST}" "${MQTT_PORT:-1883}" 30 || {
        log "⚠️ MQTT non accessible, continuons sans MQTT"
    }
fi

# Configuration finale
log "⚙️ Configuration finale..."
log "  - Mode: ${ENV:-development}"
log "  - Debug: ${DEBUG:-true}"
log "  - Log Level: ${LOG_LEVEL:-INFO}"
log "  - Workers: ${UVICORN_WORKERS:-1}"

# Démarrer l'application FastAPI avec Uvicorn
log "🎯 Démarrage de l'API FastAPI..."
log "🌐 Application accessible sur http://0.0.0.0:8000"

# Convertir LOG_LEVEL en minuscules pour uvicorn
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${UVICORN_WORKERS:-1}" \
  --access-log \
  --log-level "$UVICORN_LOG_LEVEL" \
  --loop uvloop \
  --no-use-colors
