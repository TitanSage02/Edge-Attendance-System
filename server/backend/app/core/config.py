"""
Configuration centrale de l'application Edge Attendance System API.

Ce module définit les paramètres de configuration de l'application, notamment les secrets,
les URLs, et les paramètres de connexion à la base de données et aux services externes.
Il est crucial de ne jamais coder en dur les secrets et de les fournir via des variables d'environnement.
"""

import os
import secrets
import base64
from typing import List, Optional, Union
from pydantic import field_validator, Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Classe de configuration centrale utilisant Pydantic BaseSettings.
    Cette classe charge automatiquement les variables d'environnement
    et fournit des valeurs par défaut pour les paramètres optionnels.
    """
    
    # ---------------------------------------------------------------
    # Informations sur le projet
    # ---------------------------------------------------------------
    PROJECT_NAME: str = "Edge Attendance System API"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = "API de gestion de présence avec authentification RFID et faciale"
    PROJECT_URL: str = ""
    
    # ---------------------------------------------------------------
    # Sécurité et authentification
    # ---------------------------------------------------------------
    JWT_ACCESS_SECRET: str = Field(..., env="JWT_ACCESS_SECRET")
    JWT_REFRESH_SECRET: str = Field(..., env="JWT_REFRESH_SECRET")
    
    ACCESS_TTL_MINUTES: int = Field(90, env="ACCESS_TTL_MINUTES")
    REFRESH_TTL_DAYS: int = Field(15, env="REFRESH_TTL_DAYS")

    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    
    # ---------------------------------------------------------------
    # Base de données
    # ---------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI: str = Field(..., env="SQLALCHEMY_DATABASE_URI")
    
    @field_validator("SQLALCHEMY_DATABASE_URI")
    def validate_db_url(cls, v):
        """Vérifie que l'URL de la base de données est valide."""
        if not v:
            raise ValueError("L'URL de la base de données est requise")
        return v


    DB_LOG_LEVELS : List[str] = Field(["ERROR", "CRITICAL", "INFO"], env="DB_LOG_LEVELS")
    # ---------------------------------------------------------------
    # Configuration CORS
    # ---------------------------------------------------------------
    PROJECT_BACKEND_CORS_ORIGINS: List[str] = ["*"]
    PROJECT_BACKEND_CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("PROJECT_BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Valide et prépare les origines CORS."""
        if isinstance(v, str):
            # Si c'est une chaîne JSON
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            # Sinon, c'est une liste séparée par des virgules
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Format CORS invalide: {v}")

    # ---------------------------------------------------------------
    # Configuration email
    # ---------------------------------------------------------------
    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: str = Field(..., env="SMTP_PORT")
    SMTP_USER: str = Field(..., env="SMTP_USER")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    SMTP_FROM: str = Field(..., env="SMTP_FROM")
    SMTP_FROM_NAME: str = Field(..., env="SMTP_FROM_NAME")
    SMTP_STARTTLS: bool = True

    # ---------------------------------------------------------------
    # Configuration MQTT
    # ---------------------------------------------------------------
    MQTT_HOST: str = Field("", env="MQTT_HOST")
    MQTT_PORT: int = Field(1883, env="MQTT_PORT")
    MQTT_USER: str = Field("crec_backend", env="MQTT_USER")
    MQTT_PASSWORD: str = Field("", env="MQTT_PASSWORD")
    MQTT_CA_CERT: Optional[str] = Field(None, env="MQTT_CA_CERT")
    MQTT_CLIENT_CERT: Optional[str] = Field(None, env="MQTT_CLIENT_CERT")
    MQTT_CLIENT_KEY: Optional[str] = Field(None, env="MQTT_CLIENT_KEY")
    MQTT_USE_TLS: bool = Field(False, env="MQTT_USE_TLS")

    @property
    def mqtt_host(self) -> str:
        return self.MQTT_HOST
    
    @property
    def mqtt_port(self) -> int:
        return self.MQTT_PORT
    
    @property
    def mqtt_user(self) -> str:
        return self.MQTT_USER
    
    @property
    def mqtt_password(self) -> str:
        return self.MQTT_PASSWORD
    
    @property
    def MQTT_BROKER(self) -> str:
        """Construit l'URL du broker MQTT"""
        protocol = "mqtts" if self.MQTT_USE_TLS else "mqtt"
        auth = f"{self.MQTT_USER}:{self.MQTT_PASSWORD}@" if self.MQTT_USER else ""
        return f"{protocol}://{auth}{self.MQTT_HOST}:{self.MQTT_PORT}"    
    
    # ---------------------------------------------------------------
    # Encryptage AES-256
    # ---------------------------------------------------------------
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")

    @field_validator("ENCRYPTION_KEY")
    def validate_encryption_key(cls, v):
        """Valide la clé d'encryptage, la génère ou l'encode si nécessaire."""
        if not v:
            # Génère une nouvelle clé si non fournie
            key = secrets.token_bytes(32)  # 32 octets = 256 bits (AES-256)
            return base64.b64encode(key).decode('utf-8')
        
        # Si la clé est fournie mais n'est pas au format base64
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("La clé d'encryptage doit être de 32 octets (256 bits) pour AES-256")
        except:
            # Si ce n'est pas du base64 valide, essayer d'encoder la chaîne brute
            key = v.encode('utf-8')
            # Ajuste la longueur à 32 octets
            if len(key) < 32:
                key = key.ljust(32, b'\0')
            elif len(key) > 32:
                key = key[:32]
            return base64.b64encode(key).decode('utf-8')
        
        return v
    
    # ---------------------------------------------------------------
    # Modules et certificats
    # ---------------------------------------------------------------
    CERT_RENEW_BEFORE_DAYS: int = Field(30, env="CERT_RENEW_BEFORE_DAYS")
    
    # ---------------------------------------------------------------
    # Configuration du serveur
    # ---------------------------------------------------------------
    DEBUG: bool = Field(False, env="DEBUG")
    SERVER_HOST: str = Field("0.0.0.0", env="SERVER_HOST")
    SERVER_PORT: int = Field(8000, env="SERVER_PORT")
    LOG_LEVEL: str = Field("DEBUG", env="LOG_LEVEL")
    
    # ---------------------------------------------------------------
    # Configuration WebSocket
    # ---------------------------------------------------------------
    WS_MAX_CONNECTIONS: int = Field(1000, env="WS_MAX_CONNECTIONS")
    WS_MAX_CONNECTIONS_PER_CHANNEL: int = Field(200, env="WS_MAX_CONNECTIONS_PER_CHANNEL")
    WS_HISTORY_SIZE: int = Field(100, env="WS_HISTORY_SIZE")

    # ---------------------------------------------------------------
    # Configuration du premier utilisateur administrateur
    # ---------------------------------------------------------------
    FIRST_USER_EMAIL: str = Field(..., env="FIRST_USER_EMAIL")
    FIRST_USER_FIRST_NAME: str = Field(..., env="FIRST_USER_FIRST_NAME")
    FIRST_USER_LAST_NAME: str = Field(..., env="FIRST_USER_LAST_NAME")

    # ---------------------------------------------------------------
    # # Configuration de sauvegarde système
    # ---------------------------------------------------------------
    BACKUP_DIR: str = Field("/backend-crec/data/backups", env="BACKUP_DIR")
    BACKUP_MAX_COUNT: int = Field(10, env="BACKUP_MAX_COUNT")
    BACKUP_COMPRESSION_LEVEL: int = Field(6, env="BACKUP_COMPRESSION_LEVEL")
    BACKUP_LOGS_RETENTION_DAYS: int = Field(7, env="BACKUP_LOGS_RETENTION_DAYS")
    
    # Chemins des éléments à sauvegarder
    BACKUP_CONFIG_DIR: str = Field("/backend-crec/data", env="BACKUP_CONFIG_DIR")
    BACKUP_LOGS_DIR: str = Field("/backend-crec/logs", env="BACKUP_LOGS_DIR")
    BACKUP_ENV_FILE: str = Field(".env", env="BACKUP_ENV_FILE")

    # ---------------------------------------------------------------
    # Configuration du module de reconnaissance faciale
    # ---------------------------------------------------------------
    FACE_MODEL_PATH: str = Field("app/services/face_recognition", env="FACE_MODEL_PATH")
    FACE_MODEL_CONFIDENCE_THRESHOLD: float = Field(0.5, env="FACE_MODEL_CONFIDENCE_THRESHOLD")


    # ---------------------------------------------------------------
    # Configuration RAG et Chatbot
    # ---------------------------------------------------------------
    USE_CHATBOT : bool = Field(False, env="USE_CHATBOT")
    CHATBOT_API_KEY: str = Field("", env="CHATBOT_API_KEY")
    CHATBOT_MODEL_NAME: str = Field("gemini-1.5-flash", env="CHATBOT_MODEL_NAME")    
    # Configuration ChromaDB
    VECTOR_DB_PATH: str = Field("/backend-crec/vector_db/chroma_db", env="VECTOR_DB_PATH")
    VECTOR_DB_COLLECTION_NAME: str = Field("crec_presence_logs", env="VECTOR_DB_COLLECTION_NAME")
    EMBEDDING_MODEL: str = Field("models/text-embedding-004", env="EMBEDDING_MODEL")
    # Configuration du reset de la base vectorielle
    VECTOR_DB_RESET_ON_STARTUP: bool = Field(True, env="VECTOR_DB_RESET_ON_STARTUP")
    VECTOR_DB_BACKUP_BEFORE_RESET: bool = Field(True, env="VECTOR_DB_BACKUP_BEFORE_RESET")
    
    # ---------------------------------------------------------------
    # Configuration de la surveillance des logs
    # ---------------------------------------------------------------
    LOG_MONITORING_RETENTION_DAYS : int = Field(90, env="LOG_MONITORING_RETENTION_DAYS")
    
    # Configuration du surveillance des logs
    LOG_DIR: str = Field("/backend-crec/logs", env="LOG_DIR")
    LOG_FILE_PATH: str = Field("/backend-crec/logs/app.log", env="LOG_FILE_PATH")

    # Fichier de configuration
    SETTINGS_FILE_PATH: str = Field("/backend-crec/data/settings.json", env="SETTINGS_FILE_PATH")

    @property
    def backup_database_path(self) -> str:
        """Extrait le chemin de la base de données depuis l'URI."""
        return self.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "").replace("postgresql://", "").replace("postgresql+psycopg2://", "")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = "allow"
        
        # Pour des raisons de sécurité, ne pas afficher les secrets dans les logs ou erreurs
        json_encoders = {
            SecretStr: lambda v: "***" if v else None
        }
    
# Instance singleton de la configuration
settings = Settings()