"""
Configuration de session SQLAlchemy avec système de création automatique des tables.
Ce module remplace Alembic par un système automatique basé sur create_all().
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Moteur de base de données asynchrone
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,  # Vérifie la validité de la connexion
    pool_size=5,         # Réduit pour PostgreSQL
    max_overflow=10,     # Réduit pour PostgreSQL
    pool_timeout=30,     # Timeout pour obtenir une connexion du pool
    pool_recycle=1800,   # Recycle les connexions après 30 minutes
    echo=settings.DEBUG, # Log des requêtes SQL en mode debug
    future=True,         # Utilise les fonctionnalités futures de SQLAlchemy
)

# Fabrique de sessions asynchrones
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
