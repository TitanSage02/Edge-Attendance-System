# Script d'initialisation de la base de données PostgreSQL
# Ce script est exécuté automatiquement au premier démarrage du conteneur PostgreSQL

set -e

echo "🚀 Initialisation de la base de données Edge Attendance System..."

# Créer l'utilisateur applicatif et la base de données
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
    -- Créer l'utilisateur applicatif s'il n'existe pas déjà
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$POSTGRES_USER') THEN
            CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
        END IF;
    END
    \$\$;

    -- Créer la base de données POSTGRES_DB si elle n'existe pas déjà
    SELECT 'CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER' 
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB')\gexec
EOSQL

# Configurer les permissions sur la nouvelle base de données
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname $POSTGRES_DB <<-EOSQL
    -- Donner les privilèges sur le schéma public
    GRANT ALL ON SCHEMA public TO $POSTGRES_USER;

    -- Donner les privilèges sur toutes les tables existantes et futures
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $POSTGRES_USER;

    -- Extensions PostgreSQL utiles
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Afficher les informations de configuration
    SELECT current_database() as database_name;
    SELECT usename as users FROM pg_user WHERE usename IN ('$POSTGRES_USER');
    SELECT extname as extensions FROM pg_extension;
EOSQL

echo "✅ Base de données Edge Attendance System initialisée avec succès"
echo "👤 Utilisateur applicatif créé: $POSTGRES_USER"
echo "🗄️ Base de données créée: $POSTGRES_DB"
echo "🔧 Extensions PostgreSQL installées: uuid-ossp, pg_trgm, pgcrypto"
