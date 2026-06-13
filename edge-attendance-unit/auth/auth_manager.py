"""
Gestionnaire d'authentification pour le système Edge Attendance System
Combine la reconnaissance faciale et l'authentification RFID
"""

import asyncio
import logging

import time

from utils.logger import setup_logger
from typing import Dict, Optional, Tuple, Union
from datetime import datetime

from data_manager import DataManager
from sensors.camera import CameraController
from sensors.rfid import RFIDController
from config import config

class AuthenticationResult:
    """Classe pour encapsuler le résultat de l'authentification"""
    def __init__(self, 
                 success: bool,
                 student_id: Optional[str] = None,
                 method: Optional[str] = "both",  # 'face', 'rfid', 'both'
                 error: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 confidence: Optional[float] = None):
        self.success = success
        self.student_id = student_id
        self.method = method  # 'face', 'rfid', 'both'
        self.error = error
        self.timestamp = timestamp or datetime.now()
        self.confidence = confidence  # Niveau de confiance (pour reconnaissance faciale)
        
    def to_dict(self) -> Dict:
        """Convertit le résultat en dictionnaire"""
        result = {
            "success": self.success,
            "student_id": self.student_id,
            "method": self.method,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }
        
        # Ajouter le niveau de confiance s'il est disponible
        if self.confidence is not None:
            result["confidence"] = self.confidence
            
        return result

class AuthenticationManager:
    """
    Gestionnaire d'authentification qui combine:
    - Reconnaissance faciale via CameraController
    - Identification RFID via RFIDController
    - Validation croisée des deux méthodes
    """
    
    def __init__(self, 
                 data_manager: DataManager, 
                 camera_controller: CameraController, 
                 rfid_controller: Optional[RFIDController] = None):
        
        self.data_manager = data_manager
        self.camera_controller = camera_controller
        self.rfid_controller = rfid_controller
        self.failure_count = 0
        self.config = config
        
        self.logger = setup_logger(
            name="Auth Manager",
            level=logging.INFO,
            console_level=logging.INFO
        )
        
        # Timeout pour l'authentification (en secondes)
        self.auth_timeout = 4.0  # Augmenté à 4 secondes pour permettre aux deux méthodes d'avoir le temps de s'exécuter

    async def authenticate_student(self) -> AuthenticationResult:
        """
        Lance l'authentification parallèle (face + RFID)
        
        Returns:
            AuthenticationResult: Résultat de l'authentification
        """
      
        self.logger.info("Démarrage de l'authentification bimodale...")
        
        try:
            # Exécution parallèle des deux méthodes d'authentification
            rfid_task = asyncio.create_task(self.process_rfid_reading())
            face_task = asyncio.create_task(self.process_face_recognition()) 
            
            # Attendre les deux tâches avec timeout
            done, pending = await asyncio.wait(
                [face_task, rfid_task],
                timeout=self.auth_timeout,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Annuler les tâches en attente si timeout
            for task in pending:
                task.cancel()
            
            # Récupérer les résultats
            face_result = face_task.result() if face_task in done else (None, None)
            if isinstance(face_result, tuple) and len(face_result) == 2:
                face_student_id, face_confidence = face_result
            else:
                face_student_id = face_result  # Compatibilité avec ancien format
                face_confidence = None
                
            rfid_student_id = rfid_task.result() if rfid_task in done else None
            
            # Analyser les résultats
            if face_student_id and rfid_student_id:
                # Vérifier la correspondance des deux méthodes
                if self.validate_match(face_student_id, rfid_student_id):
                    self.logger.info(f"✅ Authentification réussie pour {face_student_id} (bimodale)")
                    
                    # Réinitialiser le compteur d'échecs
                    self.failure_count = 0  
                    
                    return AuthenticationResult(
                        success=True,
                        student_id=face_student_id,
                        method="both",
                        confidence=face_confidence
                    )
                else:
                    error_msg = "Incohérence entre reconnaissance faciale et RFID"
                    self.logger.warning(f"❌ {error_msg}")
                    return AuthenticationResult(success=False, error=error_msg)
            
            elif face_student_id:
               
                self.logger.info(f"✅ Authentification réussie pour {face_student_id} (facial uniquement)")
                return AuthenticationResult(
                    success=False,
                    student_id=face_student_id,
                    method="face",
                    confidence=face_confidence
                )
                
            elif rfid_student_id:
                self.logger.info(f"✅ Authentification réussie pour {rfid_student_id} (RFID uniquement)")
                return AuthenticationResult(
                    success=False,
                    student_id=rfid_student_id,
                    method="rfid",
                    confidence=1.0  # RFID est une correspondance parfaite
                )
                
            else:
                error_msg = "Aucune méthode d'authentification n'a abouti"
                self.logger.warning(f"❌ {error_msg}")
                self.failure_count += 1
                return AuthenticationResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors de l'authentification: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.failure_count += 1
            return AuthenticationResult(success=False, error=error_msg)

    async def process_face_recognition(self) -> Tuple[Optional[str], Optional[float]]:
        """
        Processus de reconnaissance faciale
        
        Returns:
            Tuple[str, float]: ID de l'étudiant reconnu et niveau de confiance, ou (None, None) si échec
        """
        try:
            # Capturer une image et extraire l'embedding
            try:
                embedding = await self.camera_controller.capture_and_extract()
            except Exception as e:
                self.logger.error(f"Erreur lors de la capture et extraction: {e}")
                return None, None
            
            if embedding is not None:
                # Rechercher dans ChromaDB
                student_id, confidence = self.data_manager.find_matching_student(
                    embedding, self.config.SIMILARITY_THRESHOLD
                )
                if student_id:
                    self.logger.info(f"👤 Visage reconnu: étudiant {student_id} (confiance: {confidence:.2f})")
                else:
                    self.logger.warning("👤 Aucun visage correspondant trouvé")
                    
                return student_id, confidence
            else:
                self.logger.warning("📷 Impossible d'extraire un embedding facial")
                return None, None
                
        except Exception as e:
            self.logger.error(f"📷 Erreur reconnaissance faciale: {e}")
            # Log la stack trace pour faciliter le débogage
            import traceback
            self.logger.debug(f"Détail de l'erreur: {traceback.format_exc()}")
            # Incrémenter le compteur d'erreurs
            self.failure_count += 1
            return None, None
    
    async def process_rfid_reading(self) -> Optional[str]:
        """
        Processus de lecture RFID
        
        Returns:
            str: ID de l'étudiant identifié par RFID, ou None si échec
        """
        # Si le contrôleur RFID n'est pas disponible
        if self.rfid_controller is None:
            self.logger.warning("💳 Lecteur RFID non disponible")
            return None
            
        try:
            # Attendre la lecture d'une carte RFID
            rfid_uid = await self.rfid_controller.read_async(timeout=self.auth_timeout)
            
            if rfid_uid:
                # Rechercher l'étudiant par UID RFID
                student_id = self.data_manager.get_student_by_rfid(rfid_uid)
                if student_id:
                    self.logger.info(f"💳 Carte RFID reconnue: étudiant {student_id}")
                else:
                    self.logger.warning(f"💳 Carte RFID non reconnue: {rfid_uid}")
                    
                return student_id
            else:
                self.logger.info("💳 Aucune carte RFID présentée")
                return None
                
        except asyncio.TimeoutError:
            self.logger.info("⏱️ Timeout lecture RFID")
            return None
            
        except Exception as e:
            self.logger.error(f"💳 Erreur lecture RFID: {e}")
            # Log la stack trace pour faciliter le débogage
            import traceback
            self.logger.debug(f"Détail de l'erreur RFID: {traceback.format_exc()}")
            # Incrémenter le compteur d'erreurs
            self.failure_count += 1
            return None

    def validate_match(self, face_student_id: str, rfid_student_id: str) -> bool:
        """
        Valide la correspondance des deux IDs
        
        Args:
            face_student_id: ID étudiant par reconnaissance faciale
            rfid_student_id: ID étudiant par RFID
            
        Returns:
            bool: True si les deux IDs correspondent
        """
        if face_student_id == rfid_student_id:
            return True
            
        self.logger.error(f"⚠️ Mismatch: visage={face_student_id} / RFID={rfid_student_id}")
        self.failure_count += 1
        return False