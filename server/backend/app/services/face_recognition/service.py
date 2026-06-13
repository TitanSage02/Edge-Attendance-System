"""
Service de reconnaissance faciale utilisant InsightFace avec MobileFaceNet
Version optimisée avec gestion asynchrone appropriée des logs
"""

import cv2
import numpy as np
import insightface
from typing import List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from pathlib import Path
from app.core.config import settings as config
from app.services.log_service import db_logger

class FaceRecognitionService:
    """Service de reconnaissance faciale pour l'extraction d'embeddings"""
    
    def __init__(self):
        """Initialise le service avec InsightFace et MobileFaceNet"""
        try:
            self.models_path = Path(config.FACE_MODEL_PATH)

            # Initialisation de InsightFace avec MobileFaceNet
            self.app = insightface.app.FaceAnalysis(
                providers=['CPUExecutionProvider'],
                allowed_modules=['detection', 'recognition'], # Détection et reconnaissance de visage
                root=self.models_path
            )
            
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
            # Configurer les seuils de qualité
            self.min_face_size = 32  # Taille minimum du visage en pixels
            self.quality_threshold = 0.3  # Seuil de qualité pour la détection
            self.min_resolution = (112, 112)  # Résolution minimum de l'image
            
            # Pool de threads pour le traitement asynchrone
            self.executor = ThreadPoolExecutor(max_workers=4)
            
            # Flag pour savoir si le logging asynchrone est initialisé
            self._logging_initialized = True
            
        except Exception as e:
            # Log de base avec le logger Python standard pendant l'initialisation
            logging.error(f"Erreur lors de l'initialisation du service: {e}")
            raise
    
    async def initialize_logging(self):
        """Initialise le logging asynchrone après l'instantiation"""
        try:
            await db_logger.info(
                "FaceRecognitionService initialisé avec succès",
                source="face_recognition_service"
            )
            self._logging_initialized = True
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation du logging asynchrone: {e}")
    
    async def extract_embeddings(self, image: bytes) -> np.ndarray:
        """
        Extrait les embeddings d'une image

        Args:
            image: Image en bytes
            
        Returns:
            Embedding (512D) pour l'image valide

        Raises:
            RuntimeError: Si aucun visage n'est détecté
        """
        try:
            # Traitement de l'image 
            embedding = await self._process_single_image(image)
            
            if embedding is None:
                raise RuntimeError("Aucun embedding n'a pu être extrait de l'image fournie")

            return embedding
            
        except Exception as e:
            if self._logging_initialized:
                await db_logger.error(
                    f"Erreur lors de l'extraction des embeddings: {e}",
                    source="face_recognition_service"
                )
            else:
                logging.error(f"Erreur lors de l'extraction des embeddings: {e}")
            raise
    
    async def _process_single_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Traite une seule image pour extraire son embedding
        
        Args:
            image_bytes: Image en bytes
            
        Returns:
            Embedding 512D ou None si échec
        """
        try:
            # Préprocessing de l'image
            image = await self._preprocess_image_async(image_bytes)
            if image is None:
                return None
            
            # Détection de visage et extraction d'embedding
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor, 
                self._extract_face_embedding, 
                image
            )
            
            return embedding
            
        except Exception as e:
            if self._logging_initialized:
                await db_logger.error(
                    f"Erreur lors du traitement de l'image: {e}",
                    source="face_recognition_service"
                )
            else:
                logging.error(f"Erreur lors du traitement de l'image: {e}")
            return None
    
    async def _preprocess_image_async(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Préprocessing asynchrone d'une image
        
        Args:
            image_bytes: Image en bytes
            
        Returns:
            Image preprocessée ou None si erreur
        """
        try:
            # Exécuter le préprocessing dans un thread séparé
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                self.executor,
                self._preprocess_image_sync,
                image_bytes
            )
            return image
            
        except Exception as e:
            if self._logging_initialized:
                await db_logger.error(
                    f"Erreur lors du préprocessing asynchrone: {e}",
                    source="face_recognition_service"
                )
            else:
                logging.error(f"Erreur lors du préprocessing asynchrone: {e}")
            return None
    
    def _preprocess_image_sync(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Préprocessing synchrone d'une image (exécuté dans un thread)
        
        Args:
            image_bytes: Image en bytes
            
        Returns:
            Image preprocessée ou None si erreur
        """
        try:
            # Décodage de l'image depuis les bytes
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None
            
            # Conversion BGR vers RGB (InsightFace attend du RGB)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Validation de la qualité de l'image
            if not self._validate_image_quality_sync(image):
                return None
            
            # Redimensionnement si l'image est trop grande (optimisation)
            image = self._resize_image_if_needed(image)
            
            return image
            
        except Exception as e:
            logging.error(f"Erreur lors du préprocessing synchrone: {e}")
            return None
    
    def _extract_face_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrait l'embedding d'un visage depuis une image (exécuté dans un thread)

        Args:
            image: Image preprocessée

        Returns:
            Embedding 512D ou None si aucun visage détecté
        """
        try:
            # Détection de visage sur l'image
            faces = self.app.get(image)
            
            if not faces:
                return None
            
            # Prendre le visage avec le score de confiance le plus élevé
            best_face = max(faces, key=lambda x: x.det_score)
            
            # Vérifier la qualité du visage détecté
            if best_face.det_score < self.quality_threshold:
                return None
            # L'embedding est déjà calculé par InsightFace
            embedding = best_face.embedding
            
            # Normalisation de l'embedding (InsightFace ne le fait pas automatiquement)
            embedding_norm = np.linalg.norm(embedding)
            if embedding_norm > 0:
                embedding = embedding / embedding_norm
            
            # Validation de l'embedding (doit être 512D et normalisé)
            if not self._validate_embedding_quality(embedding):
                return None
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction d'embedding: {e}")
            return None
    
    def _validate_image_quality_sync(self, image: np.ndarray) -> bool:
        """
        Valide la qualité d'une image (version synchrone)
        
        Args:
            image: Image à valider
            
        Returns:
            True si l'image respecte les critères de qualité
        """
        try:
            # Vérifier les dimensions
            if image is None or len(image.shape) != 3:
                return False
            
            height, width = image.shape[:2]
            
            # Résolution minimum
            if height < self.min_resolution[1] or width < self.min_resolution[0]:
                return False
            
            # Vérifier que l'image n'est pas complètement noire ou blanche
            mean_val = np.mean(image)
            if mean_val < 10 or mean_val > 245:
                return False

            # Vérifier le contraste (écart-type des pixels)
            std_val = np.std(image)
            if std_val < 15:  # Image trop uniforme
                return False

            return True

        except Exception as e:
            logging.error(f"Erreur lors de la validation de qualité: {e}")
            return False
    
    def _resize_image_if_needed(self, image: np.ndarray) -> np.ndarray:
        """
        Redimensionne l'image si nécessaire pour l'optimisation
        
        Args:
            image: Image à redimensionner
            
        Returns:
            Image redimensionnée
        """
        height, width = image.shape[:2]
        max_size = 1024
        
        if max(height, width) > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image
    
    def _validate_embedding_quality(self, embedding: np.ndarray) -> bool:
        """
        Valide la qualité d'un embedding
        
        Args:
            embedding: Embedding à valider
            
        Returns:
            True si l'embedding est valide
        """
        try:
            # Vérifier les dimensions (doit être 512D pour MobileFaceNet)
            if embedding.shape != (512,):
                return False

            # Vérifier que l'embedding n'est pas composé que de zéros
            if np.allclose(embedding, 0):
                return False

            # Vérifier la norme de l'embedding (doit être normalisé)
            norm = np.linalg.norm(embedding)
            if not (0.9 <= norm <= 1.1):  # Tolérance pour les erreurs de précision
                return False

            # Vérifier qu'il n'y a pas de valeurs NaN ou infinies
            if not np.isfinite(embedding).all():
                return False

            return True

        except Exception as e:
            logging.error(f"Erreur lors de la validation d'embedding: {e}")
            return False
    
    async def calculate_similarity_async(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings (version asynchrone)
        
        Args:
            embedding1: Premier embedding
            embedding2: Deuxième embedding
            
        Returns:
            Score de similarité entre -1 et 1
        """
        try:
            # Exécuter le calcul dans un thread pour éviter de bloquer
            loop = asyncio.get_event_loop()
            similarity = await loop.run_in_executor(
                self.executor,
                self._calculate_similarity_sync,
                embedding1,
                embedding2
            )
            return similarity
            
        except Exception as e:
            if self._logging_initialized:
                await db_logger.error(
                    f"Erreur lors du calcul de similarité: {e}",
                    source="face_recognition_service"
                )
            else:
                logging.error(f"Erreur lors du calcul de similarité: {e}")
            return 0.0
    
    def _calculate_similarity_sync(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings (version synchrone)
        
        Args:
            embedding1: Premier embedding
            embedding2: Deuxième embedding
            
        Returns:
            Score de similarité entre -1 et 1
        """
        try:
            # Normaliser les embeddings si nécessaire
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calcul de la similarité cosinus
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logging.error(f"Erreur lors du calcul de similarité synchrone: {e}")
            return 0.0

    async def shutdown(self):
        """Arrêt propre du service"""
        try:
            if self._logging_initialized:
                await db_logger.info(
                    "Arrêt du FaceRecognitionService",
                    source="face_recognition_service"
                )
            
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
                
        except Exception as e:
            logging.error(f"Erreur lors de l'arrêt du service: {e}")

    def __del__(self):
        """Nettoyage des ressources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Instance globale
face_recognition_service = FaceRecognitionService()
