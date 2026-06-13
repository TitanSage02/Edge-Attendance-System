from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional, Dict, List, Union, Any

# ==========================================
# MODÈLES DE BASE
# ==========================================
class PresenceBase(BaseModel):
    student_id: str
    status: bool = Field(default=True, description="True pour présent, False pour absent")
    module_uid: int = Field(default=0, description="ID du module (0 pour présence manuelle)")
    timestamp: Optional[datetime] = None


# ==========================================
# SCHÉMAS DE COMMUNICATION MQTT
# ==========================================

class MQTTMessage(BaseModel):
    """Modèle de base pour les messages MQTT"""
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage du message")


# class PresenceMQTT(MQTTMessage):
#     """Schéma pour les messages de présence envoyés via MQTT"""
#     student_id: str = Field(..., description="Identifiant unique de l'étudiant")
#     status: bool = Field(default=True, description="True pour présent, False pour absent")
#     module_uid: int = Field(..., description="Identifiant unique du module de pointage")
#     timestamp: Optional[datetime] = Field(default=None, description="Horodatage de la présence")
    # details: Optional[Dict[str, Any]] = Field(default=None, description="Détails supplémentaires (méthode d'authentification, etc.)")

    # model_config = ConfigDict(
    #     json_schema_extra={
    #         "example": {
    #             "student_id": "22031996",
    #             "status": True,
    #             "module_uid": 1,
    #             "timestamp": "2025-07-02T14:30:00",
    #             "details": {"auth_method": "rfid", "confidence": 0.95}
    #         }
    #     }
    # )


class StatusMQTT(MQTTMessage):
    """Schéma pour les messages de statut envoyés via MQTT par les modules"""
    status: str = Field(..., description="État du module (online, offline, error, etc.)")
    version: str = Field(default="1.0", description="Version du logiciel")
    uptime: float = Field(default=0, description="Temps de fonctionnement en secondes")
    memory_usage: float = Field(default=0, description="Utilisation de la mémoire en pourcentage")
    cpu_usage: float = Field(default=0, description="Utilisation du CPU en pourcentage")
    ip_address: Optional[str] = Field(default=None, description="Adresse IP du module")
    module_uid: int = Field(..., description="Identifiant unique du module")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "online",
                "version": "1.0",
                "uptime": 3600,
                "memory_usage": 45.2,
                "cpu_usage": 12.5,
                "ip_address": "192.168.1.100",
                "module_uid": 1,
                "timestamp": "2025-07-02T14:30:00"
            }
        }
    )


class LogMQTT(MQTTMessage):
    """Schéma pour les messages de log envoyés via MQTT"""
    level: str = Field(..., description="Niveau de log (info, warning, error, debug)")
    message: str = Field(..., description="Message de log")
    module_uid: int = Field(..., description="Identifiant unique du module")
    source: Optional[str] = Field(default=None, description="Source du message (composant)")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Détails supplémentaires")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "level": "info",
                "message": "Module démarré avec succès",
                "module_uid": 1,
                "source": "main",
                "timestamp": "2025-07-02T14:30:00",
                "details": {"ip": "192.168.1.100"}
            }
        }
    )


class CommandMQTT(MQTTMessage):
    """Schéma pour les commandes envoyées via MQTT aux modules"""
    command: str = Field(..., description="Commande à exécuter (restart, status, update, etc.)")
    module_uid: int = Field(..., description="Identifiant unique du module cible")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Paramètres de la commande")
    sender: Optional[str] = Field(default=None, description="Identifiant de l'émetteur")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "command": "restart",
                "module_uid": 1,
                "timestamp": "2025-07-02T14:30:00",
                "params": {"timeout": 5},
                "sender": "admin"
            }
        }
    )


class ConfigUpdateMQTT(MQTTMessage):
    """Schéma pour les mises à jour de configuration envoyées via MQTT"""
    type: str = Field(..., description="Type de configuration (auth_threshold, notifications, etc.)")
    value: Any = Field(..., description="Valeur de la configuration")
    module_uid: Optional[int] = Field(default=None, description="ID du module cible (null pour tous)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "auth_threshold",
                "value": 0.75,
                "module_uid": 1,
                "timestamp": "2025-07-02T14:30:00"
            }
        }
    )


# ==========================================
# SCHÉMAS API REST 
# ==========================================

class APIResponse(BaseModel):
    """Modèle de base pour les réponses API"""
    success: bool = Field(default=True, description="Indicateur de succès de la requête")
    message: Optional[str] = Field(default=None, description="Message descriptif")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Données de la réponse")
    errors: Optional[List[str]] = Field(default=None, description="Liste des erreurs")


class AuthRequest(BaseModel):
    """Schéma pour les requêtes d'authentification API"""
    api_key: str = Field(..., description="Clé API pour l'authentification")
    module_id: int = Field(..., description="Identifiant du module")


class StudentData(BaseModel):
    """Schéma pour les données d'un étudiant"""
    student_id: str = Field(..., description="Identifiant unique de l'étudiant")
    first_name: str = Field(..., description="Prénom")
    last_name: str = Field(..., description="Nom de famille")
    class_group: Optional[str] = Field(default=None, description="Groupe/classe de l'étudiant")
    email: Optional[str] = Field(default=None, description="Email de l'étudiant")
    rfid_uid: Optional[str] = Field(default=None, description="UID RFID associé à l'étudiant")
    face_encoding: Optional[List[float]] = Field(default=None, description="Encodage facial pour reconnaissance")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "22031996",
                "first_name": "John",
                "last_name": "Doe",
                "class_group": "L1",
                "email": "john.doe@example.com",
                "rfid_uid": "A1B2C3D4",
                "face_encoding": None
            }
        }
    )


class ModuleRegistration(BaseModel):
    """Schéma pour l'enregistrement d'un nouveau module"""
    name: str = Field(..., description="Nom du module")
    location: str = Field(..., description="Lieu d'installation")
    hardware_id: str = Field(..., description="Identifiant matériel unique")
    api_key: Optional[str] = Field(default=None, description="Clé API (fournie par le serveur)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Module Entrée Principale",
                "location": "Bâtiment A, Entrée",
                "hardware_id": "RPi4-ABC123"
            }
        }
    )


# ==========================================
# TOPICS MQTT STANDARDS
# ==========================================

class MQTTTopics:
    """Classe définissant les topics MQTT standards"""
    CONFIG = "crec/modules/config_updates"
    STATUS_TEMPLATE = "crec/modules/{module_uid}/status"
    LOGS_TEMPLATE = "crec/modules/{module_uid}/logs"
    PRESENCE_TEMPLATE = "crec/modules/{module_uid}/presence"
    COMMAND_TEMPLATE = "crec/modules/{module_uid}/command"
    
    @classmethod
    def status(cls, module_uid: int) -> str:
        return cls.STATUS_TEMPLATE.format(module_uid=module_uid)
    
    @classmethod
    def logs(cls, module_uid: int) -> str:
        return cls.LOGS_TEMPLATE.format(module_uid=module_uid)
    
    @classmethod
    def presence(cls, module_uid: int) -> str:
        return cls.PRESENCE_TEMPLATE.format(module_uid=module_uid)
    
    @classmethod
    def command(cls, module_uid: int) -> str:
        return cls.COMMAND_TEMPLATE.format(module_uid=module_uid)


