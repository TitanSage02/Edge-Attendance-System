"""
Module d'initialisation automatique de la base de données.
Remplace Alembic par un système automatique basé sur SQLAlchemy create_all().
"""

import logging
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.base import Base
from app.db.session import engine

# Import tous les modèles pour s'assurer qu'ils sont enregistrés
from app.models import (
    User, RefreshToken, ApiKey, Embedding, Log, 
    Module, ModuleStatus, Presence, Student
)

logger = logging.getLogger(__name__)

async def check_database_connection(engine: AsyncEngine) -> bool:
    """
    Vérifie la connexion à la base de données.
    
    Returns:
        bool: True si la connexion est établie, False sinon
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Connexion à la base de données établie")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à la base de données: {e}")
        return False

async def get_existing_tables(engine: AsyncEngine) -> set:
    """
    Récupère la liste des tables existantes dans la base de données.
    
    Returns:
        set: Ensemble des noms de tables existantes
    """
    try:
        async with engine.begin() as conn:
            # Utilise l'inspector pour lister les tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = {row[0] for row in result.fetchall()}
        logger.info(f"📋 Tables existantes: {tables}")
        return tables
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des tables: {e}")
        return set()

async def create_missing_tables(engine: AsyncEngine) -> bool:
    """
    Crée toutes les tables définies dans les modèles qui n'existent pas encore.
    
    Returns:
        bool: True si l'opération s'est bien déroulée, False sinon
    """
    try:
        # Récupère les tables existantes
        existing_tables = await get_existing_tables(engine)
        
        # Récupère les tables définies dans les modèles
        model_tables = set(Base.metadata.tables.keys())
        logger.info(f"📝 Tables définies dans les modèles: {model_tables}")
        
        # Détermine les tables manquantes
        missing_tables = model_tables - existing_tables
        
        if not missing_tables:
            logger.info("✅ Toutes les tables existent déjà")
            return True
        
        logger.info(f"🔧 Tables à créer: {missing_tables}")
        
        # Crée toutes les tables manquantes
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Tables créées avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des tables: {e}")
        return False

async def verify_table_structure() -> bool:
    """
    Vérifie que la structure des tables correspond aux modèles.
    Note: Cette fonction fait une vérification basique.
    
    Returns:
        bool: True si la vérification s'est bien déroulée
    """
    try:
        async with engine.begin() as conn:
            # Vérifie quelques tables critiques
            critical_tables = ['users', 'modules', 'presences']
            
            for table in critical_tables:
                result = await conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND table_schema = 'public'
                """))
                columns = [row[0] for row in result.fetchall()]
                
                if columns:
                    logger.info(f"✅ Table '{table}' vérifiée ({len(columns)} colonnes)")
                else:
                    logger.warning(f"⚠️ Table '{table}' introuvable ou vide")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        return False

async def initialize_database() -> bool:
    """
    Fonction principale d'initialisation de la base de données.
    
    Cette fonction :
    1. Vérifie la connexion à la base de données
    2. Vérifie quelles tables existent
    3. Crée les tables manquantes
    4. Vérifie la structure des tables
    
    Returns:
        bool: True si l'initialisation s'est bien déroulée, False sinon
    """
    logger.info("🚀 Initialisation de la base de données...")
    
    # Étape 1: Vérifier la connexion
    if not await check_database_connection(engine):
        return False
    
    # Étape 2: Créer les tables manquantes
    if not await create_missing_tables(engine):
        return False
    
    # Étape 3: Vérifier la structure
    if not await verify_table_structure():
        return False
    
    logger.info("🎉 Initialisation de la base de données terminée avec succès")
    return True