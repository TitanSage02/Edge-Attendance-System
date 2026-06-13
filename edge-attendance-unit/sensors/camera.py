###############################
# Gestionnaire de la PiCamera #
###############################

import cv2
import numpy as np
import logging
from utils.logger import setup_logger
from typing import Optional, Tuple, List
from picamera2 import Picamera2
from insightface.app import FaceAnalysis
import io
from PIL import Image

class CameraController:
    """
    Contrôleur de caméra avec support InsightFace pour la reconnaissance faciale.
    Supporte PiCamera2 et caméras USB (via OpenCV)
    """
    
    def __init__(self, model_name: str = 'buffalo_l', camera_id: int = 1, force_usb: bool = False):
        """
        Initialise le contrôleur de caméra avec InsightFace
        
        Args:
            model_name: Nom du modèle InsightFace à utiliser ('buffalo_l', 'buffalo_m', 'buffalo_s')
            camera_id: ID de la caméra USB 
            force_usb: Force l'utilisation de la caméra USB même si une PiCamera est disponible
        """
        self.logger = setup_logger(
            name="camera",
            level=logging.INFO,
            console_level=logging.INFO
        )

        self.camera = None
        self.face_app = None
        self.model_name = model_name
        self.is_initialized = False
        self.camera_id = camera_id
        self.force_usb = force_usb
        self.using_picamera = False
        

        # Configuration qualité image et visage (aligné sur service.py)
        self.min_face_size = 32  # Taille minimum du visage en pixels
        self.quality_threshold = 0.3  # Seuil de qualité pour la détection
        self.min_resolution = (112, 112)  # Résolution minimum de l'image
        self.max_image_size = 1024  # Taille maximale pour redimensionnement
        
        # Configuration InsightFace
        self.face_config = {
            'det_thresh': self.quality_threshold,  # Aligné sur quality_threshold
            'ctx_id': -1,       # CPU: -1, GPU: 0
            'det_size': (640, 640)
        }
        
        self._initialize_camera()
        self._initialize_insightface()
    
    def _initialize_camera(self):
        """Initialise la caméra (PiCamera2 ou USB)"""
        try:
            # Essayer d'abord PiCamera2 sauf si force_usb est True
            if not self.force_usb:
                try:
                    self.camera = Picamera2()
                    
                    # Configuration de la caméra
                    camera_config = self.camera.create_preview_configuration(
                            main={"format": 'YUV420', "size": (7680, 4320)} # en HD
                    )
        
                    self.camera.configure(camera_config)
                    self.camera.start()
                    
                    actual_res = self.camera.camera_properties['PixelArraySize']
                    self.logger.info(f"📷 PiCamera2 initialisée en {actual_res[0]}x{actual_res[1]}")
                    self.using_picamera = True
                    return
                    
                except Exception as e:
                    self.logger.warning(f"PiCamera2 non disponible: {e}, tentative avec caméra USB...")
            
            # Si PiCamera2 n'est pas disponible ou force_usb=True, utiliser OpenCV
            self.camera = cv2.VideoCapture(self.camera_id)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"Impossible d'ouvrir la caméra USB {self.camera_id}")
            
            # Vérifier la résolution réelle
            actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"📷 Caméra USB initialisée en {actual_width}x{actual_height} @ {actual_fps}fps")
            self.using_picamera = False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'initialisation de la caméra: {e}")
            raise RuntimeError(f"Impossible d'initialiser la caméra: {e}")
    
    def _initialize_insightface(self):
        """Initialise le modèle InsightFace"""
        try:
            self.face_app = FaceAnalysis(name=self.model_name)
            self.face_app.prepare(
                ctx_id=self.face_config['ctx_id'],
                det_thresh=self.face_config['det_thresh'],
                det_size=self.face_config['det_size']
            )

            # Suppression des modèles inutiles
            self.face_app.models.pop('genderage', None)
            self.face_app.models.pop('landmark_2d_106', None)
            self.face_app.models.pop('landmark_3d_68', None)

            self.is_initialized = True
            self.logger.info(f"InsightFace initialisé avec le modèle {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation d'InsightFace: {e}")
            raise RuntimeError(f"Impossible d'initialiser InsightFace: {e}")
    
    def capture_photo(self) -> Optional[np.ndarray]:
        """Capture une photo depuis la caméra"""
        if not self.camera:
            self.logger.error("Caméra non initialisée")
            return None
        
        try:
            if self.using_picamera:
                frame = self.camera.capture_array()
                self.logger.warning(f"Frame capturée: {frame.shape}")
                if len(frame.shape) == 2:
                    image = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                else : 
                    image = cv2.cvtColor(frame, cv2.COLOR_YUV2RGB_I420)      
            else:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.error("Échec de la capture USB")
                    return None
                
                # Convertir BGR vers RGB pour OpenCV
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            self.logger.debug(f"Image capturée: {image.shape}")
            return image
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture: {e}")
            return None
    
    def extract_embedding(self, photo: np.ndarray) -> Optional[Tuple[np.ndarray, dict]]:
        """
        Extrait l'embedding facial avec InsightFace
        
        Args:
            photo: Image au format numpy array (RGB)
            
        Returns:
            Tuple[np.ndarray, dict]: (embedding, face_info) ou None si aucun visage détecté
            - embedding: Vecteur d'embedding facial (512D pour buffalo models)
            - face_info: Informations sur le visage détecté (bbox, landmarks, etc.)
        """

        if not self.is_initialized:
            self.logger.error("InsightFace non initialisé")
            return None
        
        if photo is None:
            self.logger.error("Photo invalide pour l'extraction d'embedding")
            return None
        
        try:
            # InsightFace attend une image RGB
            # Si l'image vient d'OpenCV (BGR), il faut la convertir
            if len(photo.shape) == 3 and photo.shape[2] == 3:
                # On assume que PiCamera2 donne du RGB
                rgb_image = photo
            else:
                self.logger.error("Format d'image non supporté")
                return None
            
            # Détection et analyse des visages
            faces = self.face_app.get(rgb_image)
            
            if not faces:
                self.logger.warning("Aucun visage détecté dans l'image")
                return None
            
            if len(faces) > 1:
                self.logger.warning(f"{len(faces)} visages détectés, utilisation du premier")

            # Prendre le visage avec le score de détection le plus élevé
            face = max(faces, key=lambda x: x.det_score)
            
            # Extraire l'embedding
            embedding = face.embedding
            
            # Normaliser l'embedding
            embedding_norm = np.linalg.norm(embedding)
            if embedding_norm > 0:
                embedding = embedding / embedding_norm
        

            # Informations sur le visage
            face_info = {
                # 'bbox': face.bbox.tolist(),  # Boîte englobante [x1, y1, x2, y2]
                'det_score': float(face.det_score),  # Score de détection
                'age': getattr(face, 'age', None),
                'gender': getattr(face, 'gender', None),
                'embedding': embedding.tolist(),  # Convertir en liste pour JSON
            }

            self.logger.debug(f"Embedding extrait: dimension {embedding.shape}, det_score {float(face.det_score):.3f}")

            return embedding
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction d'embedding: {e}")
            return None
    
    async def capture_and_extract(self) -> Optional[np.ndarray]:
        """
        Capture une image et extrait l'embedding facial
        
        Returns:
            np.ndarray: Embedding facial si un visage est détecté, None sinon
        """
        try:
            # Capture de l'image selon le type de caméra
            if self.using_picamera:
                frame = self.camera.capture_array()
                self.logger.warning(f"Frame capturée: {frame.shape}")
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                else : 
                    frame = cv2.cvtColor(frame, cv2.COLOR_YUV2RGB_I420)
            else:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.error("Échec de la capture USB")
                    return None
                # Convertir BGR vers RGB pour les caméras USB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            self.logger.debug(f"Image capturée: {frame.shape}")
            
            # Conversion RGBA en RGB si nécessaire
            if frame.shape[-1] == 4:
                self.logger.debug("Conversion RGBA vers RGB")
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            
            # # Validation de la qualité de l'image
            # if not self._validate_image_quality(frame):
            #     self.logger.warning("Image ne respecte pas les critères de qualité")
            #     return None
            
            # Redimensionnement si nécessaire
            frame = self._resize_image_if_needed(frame)
            
            # Détection et analyse du visage
            faces = self.face_app.get(frame)
            
            if not faces:
                self.logger.warning("Aucun visage détecté dans l'image")
                return None
                
            # Prendre le visage avec le meilleur score de détection
            best_face = max(faces, key=lambda x: x.det_score)
            
            # Vérifier le score de détection
            if best_face.det_score < self.quality_threshold:
                self.logger.warning(f"Score de détection trop faible: {best_face.det_score}")
                return None
            
            # Récupérer l'embedding
            embedding = best_face.embedding
            
            # Normalisation de l'embedding
            embedding_norm = np.linalg.norm(embedding)
            if embedding_norm > 0:
                embedding = embedding / embedding_norm
            
            # Validation de l'embedding
            if not self._validate_embedding_quality(embedding):
                self.logger.warning("Embedding ne respecte pas les critères de qualité")
                return None
            
            self.logger.info(f"✅ Embedding extrait avec succès (score: {best_face.det_score:.3f})")
            return embedding.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction de l'embedding: {e}")
            import traceback
            self.logger.debug(f"Détails: {traceback.format_exc()}")
            return None
  
    
    # def save_debug_image(self, photo: np.ndarray, face_info: dict, filename: str):
    #     """
    #     Sauvegarde une image avec les informations de débogage
        
    #     Args:
    #         photo: Image originale
    #         face_info: Informations sur le visage
    #         filename: Nom du fichier de sortie
    #     """
    #     try:
    #         debug_image = photo.copy()
            
    #         if face_info and 'bbox' in face_info:
    #             bbox = face_info['bbox']
    #             # Dessiner le rectangle du visage
    #             cv2.rectangle(debug_image, 
    #                         (int(bbox[0]), int(bbox[1])), 
    #                         (int(bbox[2]), int(bbox[3])), 
    #                         (0, 255, 0), 2)
                
    #             # Ajouter le score de détection
    #             score_text = f"Score: {face_info['det_score']:.3f}"
    #             cv2.putText(debug_image, score_text, 
    #                        (int(bbox[0]), int(bbox[1]) - 10),
    #                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
    #         # Sauvegarder (conversion RGB vers BGR pour OpenCV)
    #         cv2.imwrite(filename, cv2.cvtColor(debug_image, cv2.COLOR_RGB2BGR))
    #         self.logger.debug(f"Image de débogage sauvegardée: {filename}")
            
    #     except Exception as e:
    #         self.logger.error(f"Erreur lors de la sauvegarde de l'image de débogage: {e}")
    
    def get_camera_info(self) -> dict:
        """
        Retourne les informations sur la caméra
        
        Returns:
            dict: Informations sur la configuration de la caméra
        """
        return {
            'resolution': self.camera_config['resolution'],
            'framerate': self.camera_config['framerate'],
            'format': self.camera_config['format'],
            'model_name': self.model_name,
            'is_initialized': self.is_initialized,
            'face_det_thresh': self.face_config['det_thresh']
        }
    
    def cleanup(self):
        """Nettoie les ressources de la caméra"""
        try:
            if hasattr(self, 'camera') and self.camera:
                try:
                    if self.using_picamera:
                        self.camera.stop()
                        self.camera.close()
                        self.logger.info("PiCamera arrêtée et fermée")
                    else:
                        self.camera.release()
                        self.logger.info("Caméra USB libérée")
                except Exception as e:
                    self.logger.warning(f"Non-critique: Erreur lors de l'arrêt de la caméra: {e}")
                
                # Nettoyer les références
                self.camera = None
                if hasattr(self, 'face_app') and self.face_app:
                    self.face_app = None
                    
                self.logger.info("Ressources caméra libérées")
        except Exception as e:
            self.logger.error(f"Erreur lors de la fermeture de la caméra: {e}")
    
    def __del__(self):
        """Destructeur pour nettoyer automatiquement"""
        if hasattr(self, 'logger'):
            try:
                self.cleanup()
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Erreur lors du nettoyage caméra dans le destructeur: {e}")
        elif hasattr(self, 'camera') and self.camera:
            try:
                self.camera.close()
            except:
                pass
    
    def _validate_image_quality(self, image: np.ndarray) -> bool:
        """
        Valide la qualité d'une image
        
        Args:
            image: Image à valider
            
        Returns:
            True si l'image respecte les critères de qualité
        """
        try:
            # Vérifier les dimensions
            if image is None or len(image.shape) != 3:
                self.logger.warning("Format d'image invalide")
                return False
            
            height, width = image.shape[:2]
            
            # Résolution minimum
            if height < self.min_resolution[1] or width < self.min_resolution[0]:
                self.logger.warning(f"Résolution trop faible: {width}x{height}")
                return False
            
            # # Vérifier que l'image n'est pas complètement noire ou blanche
            # mean_val = np.mean(image)
            # if mean_val < 10 or mean_val > 245:
            #     self.logger.warning(f"Image trop sombre ou trop claire: moyenne={mean_val}")
            #     return False

            # # Vérifier le contraste (écart-type des pixels)
            # std_val = np.std(image)
            # if std_val < 15:  # Image trop uniforme
            #     self.logger.warning(f"Contraste trop faible: std={std_val}")
            #     return False

            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la validation de qualité: {e}")
            return False
    
    def _validate_embedding_quality(self, embedding: np.ndarray) -> bool:
        """
        Valide la qualité d'un embedding
        
        Args:
            embedding: Embedding à valider
            
        Returns:
            True si l'embedding est valide
        """
        try:
            # Vérifier les dimensions (doit être 512D pour MobileFaceNet/buffalo)
            if embedding.shape != (512,):
                self.logger.warning(f"Dimension d'embedding invalide: {embedding.shape}")
                return False

            # Vérifier que l'embedding n'est pas composé que de zéros
            if np.allclose(embedding, 0):
                self.logger.warning("Embedding nul détecté")
                return False

            # Vérifier la norme de l'embedding (doit être proche de 1)
            norm = np.linalg.norm(embedding)
            if not (0.9 <= norm <= 1.1):
                self.logger.warning(f"Norme d'embedding invalide: {norm}")
                return False

            # Vérifier qu'il n'y a pas de valeurs NaN ou infinies
            if not np.isfinite(embedding).all():
                self.logger.warning("Valeurs non finies détectées dans l'embedding")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la validation d'embedding: {e}")
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
        
        if max(height, width) > self.max_image_size:
            if width > height:
                new_width = self.max_image_size
                new_height = int(height * (self.max_image_size / width))
            else:
                new_height = self.max_image_size
                new_width = int(width * (self.max_image_size / height))
            
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            self.logger.debug(f"Image redimensionnée à {new_width}x{new_height}")
            
        return image
    
    def is_camera_ok(self) -> bool:
        """Vérifie si la caméra est opérationnelle"""
        if not self.camera:
            return False
            
        if self.using_picamera:
            return True  # PiCamera2 n'a pas de méthode de vérification simple
        else:
            return self.camera.isOpened()