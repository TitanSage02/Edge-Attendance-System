"""
Base SQLAlchemy pour le système automatique de création de tables.
Cette base remplace Alembic par un système create_all() automatique.
"""

from sqlalchemy.ext.declarative import declarative_base

# Base déclarative pour tous les modèles
# Toutes les classes de modèles doivent hériter de cette base
Base = declarative_base()