########################################
## Gestion des données et de ChromaDB ##
########################################

import chromadb
import logging
import aiohttp
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from config import config
from schemas.schema import StudentData, APIResponse

# Désactivation explicite de la télémétrie
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
from utils.logger import setup_logger

class DataManager:
    """
    Gestionnaire de données responsable de:
    1. Récupération des données étudiants depuis l'API
    2. Stockage local des embeddings dans ChromaDB
    3. Recherche des étudiants par similarité d'embedding
    4. Cache des données pour le mode hors-ligne
    """
    
    def __init__(self):
        self.logger = setup_logger(
            name="Data Manager",
            level=logging.INFO,
            console_level=logging.INFO
        )
        self.chroma_client = chromadb.Client()
        self.collection = None
        self.api_base_url = config.BASE_URL
        self.api_key = config.API_KEY
        self.module_id = config.MODULE_ID
        
        # Cache des données
        self.students_cache = {}
        self.last_sync_time = None
        self.sync_interval = timedelta(minutes=15)  # Synchronise toutes les 15 minutes

        # Initialisation de ChromaDB
        self._initialize_collection()
        
    def _initialize_collection(self):
        """Initialise la collection ChromaDB pour les embeddings faciaux"""
        try:
            # Création ou récupération de la collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="student_embeddings",
                metadata={"hnsw:space": "cosine"}  # Espace de similarité cosinus
            )
            self.logger.info("Collection ChromaDB initialisée avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de ChromaDB: {e}")
            raise RuntimeError(f"Impossible d'initialiser ChromaDB: {e}")
    
    async def fetch_students_data(self) -> Dict:
        """
        Récupère les données des étudiants via l'API REST
        
        Returns:
            Dict: Dictionnaire contenant les données des étudiants et leurs embeddings
        """
        # Vérifier si une synchronisation est nécessaire
        if (self.last_sync_time and 
            datetime.now() - self.last_sync_time < self.sync_interval and
            self.students_cache):
            
            cache_age_minutes = (datetime.now() - self.last_sync_time).total_seconds() / 60
            students_count = len(self.students_cache)
            
            self.logger.info(f"📊 CACHE: Utilisation des données en cache ({students_count} étudiants, âge: {cache_age_minutes:.1f} minutes)")
            self.logger.debug(f"CACHE: Prochaine synchronisation prévue dans {(self.sync_interval.total_seconds()/60) - cache_age_minutes:.1f} minutes")
            return self.students_cache
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                
                # Endpoint pour récupérer les étudiants associés au module
                url = f"{self.api_base_url}/api/v1/students/data"
                
                self.logger.info(f"Récupération des données étudiants depuis {url}")

                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Erreur API {response.status}: {error_text}")
                        
                        # Si données en cache disponibles, les utiliser en mode dégradé
                        if self.students_cache:
                            cache_age_minutes = (datetime.now() - self.last_sync_time).total_seconds() / 60 if self.last_sync_time else None
                            students_count = len(self.students_cache)
                            
                            self.logger.warning(f"⚠️ API ERROR: Utilisation des données en cache en mode dégradé ({students_count} étudiants, âge: {cache_age_minutes:.1f} minutes)")
                            return self.students_cache
                        
                        # Si pas de cache, retourner des données vides pour permettre le fonctionnement en mode test/démo
                        self.logger.warning(f"⚠️ AUCUNES DONNÉES: API inaccessible et pas de cache. Fonctionnement en mode démo.")
                        self.students_cache = {}
                        self.last_sync_time = datetime.now()
                        return self.students_cache
                    
                    students_data = await response.json()
                    
                    self.logger.debug(f"Données brutes reçues: {students_data}")

                    # Mise à jour du cache
                    self.students_cache = students_data
                    self.last_sync_time = datetime.now()
                    
                    # Stockage des embeddings dans ChromaDB
                    self.store_embeddings(students_data)
                    
                    self.logger.info(f"Récupération réussie: {len(students_data)} étudiants")
                    return students_data
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Erreur réseau lors de la récupération des données: {e}")
            # En cas d'erreur réseau, utiliser le cache si disponible
            if self.students_cache:
                cache_age_minutes = (datetime.now() - self.last_sync_time).total_seconds() / 60 if self.last_sync_time else None
                students_count = len(self.students_cache)
                
                self.logger.warning(f"🌐 NETWORK ERROR: Utilisation des données en cache ({students_count} étudiants, âge: {cache_age_minutes:.1f} minutes)")
                return self.students_cache
            
            # Si pas de cache, permettre le fonctionnement en mode démo
            self.logger.warning(f"🌐 NETWORK ERROR: Aucune donnée disponible. Fonctionnement en mode démo.")
            self.students_cache = {}
            self.last_sync_time = datetime.now()
            return self.students_cache

        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la récupération des données: {e}")
            if self.students_cache:
                cache_age_minutes = (datetime.now() - self.last_sync_time).total_seconds() / 60 if self.last_sync_time else None
                students_count = len(self.students_cache)
                
                self.logger.warning(f"⚠️ UNEXPECTED ERROR: Utilisation des données en cache ({students_count} étudiants, âge: {cache_age_minutes:.1f} minutes)")
                return self.students_cache
            
            # Si pas de cache, permettre le fonctionnement en mode démo
            self.logger.warning(f"⚠️ UNEXPECTED ERROR: Aucune donnée disponible. Fonctionnement en mode démo.")
            self.students_cache = {}
            self.last_sync_time = datetime.now()
            return self.students_cache

    def store_embeddings(self, students_data: List[Dict[str, Any]]) -> None:
        """
        Stocke les embeddings dans ChromaDB pour recherche rapide
        
        Args:
            students_data: Liste des étudiants avec leurs embeddings et leurs RFID
        """
        if not self.collection:
            self.logger.error("Collection ChromaDB non initialisée")
            return
        
        try:
            # Préparation des données pour insertion dans ChromaDB
            ids = []
            embeddings = []
            metadatas = []

            # Vider la collection avant d'insérer les nouvelles données
            try:
                self.logger.info("Suppression des anciens embeddings dans ChromaDB")
                existing_ids = [item.get("id") for item in self.collection.get()["metadatas"]]
                if existing_ids:
                    self.collection.delete(ids=existing_ids)
                    self.logger.info(f"Supprimé {len(existing_ids)} anciens embeddings")
                else:
                    self.logger.info("Aucun ancien embedding à supprimer")
            except Exception as e:
                self.logger.warning(f"Erreur lors de la suppression des anciens embeddings: {e}, continuons avec l'ajout")
            
          
            if isinstance(students_data, list):
                # Format de données: liste d'étudiants (StudentModuleRead)
                for student in students_data:
                    # Vérifier si l'étudiant a un embedding
                    # Adapter aux clés utilisées par le backend (studentId au lieu de id)
                    student_id = student.get("studentId") if isinstance(student, dict) else getattr(student, "studentId", None)
                    face_embedding = student.get("faceEmbedding") if isinstance(student, dict) else getattr(student, "faceEmbedding", None)
                    
                    if student_id and face_embedding:
                        embedding_id = f"{student_id}"
                        
                        # Métadonnées pour la récupération
                        metadata = {
                            "student_id": student_id
                        }
                        
                        ids.append(embedding_id)
                        embeddings.append(face_embedding)
                        metadatas.append(metadata)
                    else:
                        self.logger.warning(f"Données incomplètes pour un étudiant: id={student_id}, embedding={'présent' if face_embedding else 'absent'}")
                    
            # Insertion dans ChromaDB
            if ids:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                self.logger.info(f"Stockage réussi: {len(ids)} embeddings dans ChromaDB")
            else:
                self.logger.warning("Aucun embedding à stocker - Vérifier si des embeddings sont présents dans les données reçues")
        
        except Exception as e:
            self.logger.error(f"Erreur lors du stockage des embeddings: {e}")
            raise RuntimeError(f"Impossible de stocker les embeddings: {e}")
        
    def find_matching_student(self, embedding: np.ndarray, threshold: float = 0.6) -> Tuple[Optional[str], Optional[float]]:
        """
        Trouve l'étudiant correspondant à l'embedding facial
        
        Args:
            embedding: Embedding facial (numpy array)
            threshold: Seuil de similarité (0.0 à 1.0)
            
        Returns:
            Tuple[str, float]: ID de l'étudiant correspondant et score de confiance, ou (None, None) si pas de correspondance
        """
        if not self.collection:
            self.logger.error("Collection ChromaDB non initialisée")
            return None
        
        try:
            # Conversion de l'embedding numpy en liste pour ChromaDB
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            
            # Recherche des embeddings les plus proches
            results = self.collection.query(
                query_embeddings=[embedding_list],
                n_results=1  # Récupérer seulement le meilleur match
            )
            
            if results and results["distances"] and results["metadatas"]:
                # Cosine-similarity score (1.0 - cosine distance)
                similarity = 1.0 - results["distances"][0][0]

                # Similarity gate. The threshold was relaxed during the field pilot
                # because a strict value raised the False Rejection Rate under variable
                # lighting. It is configurable via SIMILARITY_THRESHOLD (default 0.6;
                # tested range 0.6–0.8) and should be calibrated on-device by the
                # operator. RFID remains the mandatory second factor.
                if similarity >= threshold:
                    student_id = results["metadatas"][0][0]["student_id"]
                    self.logger.info(f"Match trouvé: étudiant {student_id} (similarité: {similarity:.2f} ≥ {threshold})")
                    return student_id, similarity
                else:
                    self.logger.warning(f"Match insuffisant: similarité {similarity:.2f} < seuil {threshold}")
                    return None, None
            else:
                self.logger.warning("Aucun résultat trouvé dans ChromaDB")
                return None, None
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche d'embedding: {e}")
            return None, None
            
    def get_student_by_rfid(self, rfid_uid: str) -> Optional[str]:
        """
        Récupère l'ID d'un étudiant à partir de son UID RFID
        
        Args:
            rfid_uid: UID de la carte RFID
            
        Returns:
            str: ID de l'étudiant correspondant, ou None si pas de correspondance
        """
        if not self.students_cache:
            self.logger.error("Cache des étudiants non disponible")
            return None
            
        try:
            for student in self.students_cache:
                if isinstance(student, dict):
                    current_rfid = student.get("rfidUid")
                    student_id = student.get("studentId")
                else:
                    current_rfid = getattr(student, "rfidUid", None)
                    student_id = getattr(student, "studentId", None)
                    
                if current_rfid == rfid_uid and student_id:
                    self.logger.info(f"Correspondance RFID trouvée pour l'étudiant {student_id}")
                    return student_id
           
            self.logger.warning(f"Aucune correspondance RFID trouvée pour {rfid_uid}")
            return None
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche par RFID: {e}")
            return None