"""
Schémas Pydantic pour les paramètres de l'application.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class SystemSettings(BaseModel):
    """Paramètres système de l'application."""
    current_promotion: str = Field(..., description="Année académique actuelle")
    notifications_enabled: bool = Field(True, description="Notifications activées")
    max_login_attempts: int = Field(5, ge=3, le=20, description="Tentatives d'authentification maximales")
    
    @field_validator('current_promotion')
    def validate_promotion(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('La promotion ne peut pas être vide')
        return v.strip()


class BackupSettings(BaseModel):
    """Paramètres de sauvegarde système."""
    auto_backup_enabled: bool = Field(True, description="Sauvegardes automatiques activées")
    backup_frequency_hours: int = Field(24, ge=1, le=168, description="Fréquence de sauvegarde en heures")
    max_backup_files: int = Field(10, ge=1, le=50, description="Nombre maximum de fichiers de sauvegarde")
    include_database: bool = Field(True, description="Inclure la base de données dans les sauvegardes")
    include_config: bool = Field(True, description="Inclure les fichiers de configuration")
    include_logs: bool = Field(False, description="Inclure les fichiers de logs")


class AllSettings(BaseModel):
    """Tous les paramètres de l'application."""
    system: SystemSettings
    backup: BackupSettings


class SettingsUpdate(BaseModel):
    """Mise à jour partielle des paramètres."""
    system: Optional[SystemSettings] = None
    backup: Optional[BackupSettings] = None


class SettingsResponse(BaseModel):
    """Réponse des paramètres avec métadonnées."""
    settings: AllSettings
    last_updated: Optional[str] = None
    updated_by: Optional[str] = None
    message: str = "Paramètres récupérés avec succès"
