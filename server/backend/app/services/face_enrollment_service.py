"""
Service de traitement d'enrôlement facial en arrière-plan.
Gère l'extraction des embeddings à partir des photos capturées.
"""

import asyncio
import io
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from PIL import Image
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.student import Student
from app.services.student_service import get as get_student_by_id
from app.schemas.embeddings import EmbeddingCreate
from app.services.embeddings_service import (
    create_embedding,
    get_embedding_by_student,
    update_embedding
)
from app.services.mqtt_service import publish_mqtt_update
from app.services.log_service import db_logger
from app.db.session import AsyncSessionLocal

from app.services.face_recognition.service import face_recognition_service

class FaceEnrollmentProcessor:
    """
    Processeur d'enrôlement facial gérant le traitement asynchrone des photos.
    """
    
    def __init__(self):
        self.processing_jobs: Dict[str, Dict[str, Any]] = {}
    
    async def start_enrollment_processing(
        self,
        job_id: str,
        student_id: str,
        photos_data: List[bytes],
        user_id: int
    ) -> None:
        """
        Lance le traitement d'enrôlement en arrière-plan.
        
        Args:
            job_id: Identifiant unique du job de traitement
            student_id: ID de l'étudiant concerné
            photos_data: Liste des données binaires des photos
            user_id: ID de l'utilisateur qui a lancé l'enrôlement
        """

        # Initialiser le statut du job
        self.processing_jobs[job_id] = {
            "status": "processing",
            "student_id": student_id,
            "total_photos": len(photos_data),
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
            "error": None
        }
        
        # Lancer la tâche en arrière-plan
        asyncio.create_task(
            self._process_enrollment_photos(job_id, student_id, photos_data, user_id)
        )

    async def _process_enrollment_photos(
        self,
        job_id: str,
        student_id: str,
        photos_data: List[bytes],
        user_id: int
    ) -> None:
        """
        Traite les photos d'enrôlement en arrière-plan.

        Args:
            db : Session pour la bd
            job_id: Identifiant du job
            student_id: ID de l'étudiant
            photos_data: Données binaires des photos
            user_id: ID de l'utilisateur
        """

        # Nouvelle session DB indépendante pour les tâches en arrière-plan
        async with AsyncSessionLocal() as background_db:
            try:
                await db_logger.debug(
                    f"🎯 Début du traitement d'enrôlement facial pour l'étudiant {student_id} (Job: {job_id})",
                    source="face_enrollment.background_start",
                    user_id=user_id
                )

                face_embeddings = []
                processed_count = 0
                    
                # Traitement de chaque photo
                for i, photo_data in enumerate(photos_data):
                    try:
                        # Traitement de l'image
                        embedding = await self._extract_face_embedding(photo_data, i + 1)
                        
                        if embedding is not None:
                            face_embeddings.append(embedding)
                            processed_count += 1
                            
                            # Mettre à jour le statut
                            self.processing_jobs[job_id]["processed_photos"] = processed_count
                            
                            await db_logger.debug(
                                f"Photo {i + 1}/{len(photos_data)} traitée avec succès pour l'étudiant {student_id}",
                                source="face_enrollment.photo_processed",
                                user_id=user_id
                            )      

                        else:
                            await db_logger.error(
                                f"Photo {i + 1} pour l'étudiant {student_id} n'a pas pu être traitée",
                                source="face_enrollment.photo_failed",
                                user_id=user_id
                            )
                             
                        
                    except Exception as e:
                        await db_logger.error(
                            f"Échec du traitement de la photo {i + 1} pour l'étudiant {student_id}: {str(e)}",
                            "face_enrollment.photo_failed",
                            user_id=user_id
                        )

                    finally:
                        # Nettoyer les ressources si nécessaire
                        pass
                    
                    
                    if face_embeddings:
                        # Crée l'embedding final à partir de la moyenne
                        final_embedding = np.mean(face_embeddings, axis=0).tolist()
                        
                        # Sauvegarder l'embedding en base
                        await self._save_embedding(background_db, student_id, final_embedding, user_id)
                        
                        # Mettre à jour le flag d'enrôlement de l'étudiant
                        await self._update_student_enrollment_status(background_db, student_id, True)
                        
                        # Publier la nouvelle sur MQTT
                        # await publish_mqtt_update("create", student_id)

                        # Marquer le job comme terminé avec succès
                        self.processing_jobs[job_id].update(
                            {
                                "status": "completed",
                                "completed_at": datetime.now(timezone.utc)
                            }
                        )

                student_name = await get_student_by_id(background_db, student_id) 
                student_name = student_name.firstName + " " + student_name.lastName
                
                await db_logger.info(
                        f"✅ Enrôlement facial complété avec succès pour l'étudiant {student_name} (ID: {student_id}).",
                        "face_enrollment.completed",
                        user_id=user_id
                    )
                    
            except Exception as e:
                # Marquer le job comme échoué
                self.processing_jobs[job_id].update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now(timezone.utc)
                })
                    
                await db_logger.error(
                    f"❌ Échec du traitement d'enrôlement pour l'étudiant {student_id}: {str(e)}",
                    "face_enrollment.failed",
                    user_id=user_id
                )
    
    async def _extract_face_embedding(self, photo_data: bytes, photo_index: int) -> List[float]:
        """
        Extrait l'embedding facial d'une photo.
        
        Args:
            photo_data: Données binaires de la photo
            photo_index: Index de la photo pour le logging
            
        Returns:
            Liste de 128 flottants représentant l'embedding, ou None si échec
        """
        try:
            # Ouvrir et traiter l'image
            image = Image.open(io.BytesIO(photo_data))
            
            # Redimensionner si nécessaire (max 1024x1024)
            if image.width > 1024 or image.height > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convertir l'image PIL en bytes pour le service de reconnaissance faciale
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=95)
            image_bytes = img_byte_arr.getvalue()
            
            embedding = await face_recognition_service.extract_embeddings(image_bytes)
                   
            return embedding.tolist()
       
        except Exception as e:
            await db_logger.error(
                f"Erreur lors de l'extraction d'embedding pour la photo {photo_index}: {str(e)}",
                "face_enrollment.extraction_error"
            )
            return None
        
    async def _save_embedding(
        self,
        db: AsyncSession,
        student_id: str,
        embedding: List[float],
        user_id: int
    ) -> None:
        """
        Sauvegarde l'embedding facial en base de données.
        
        Args:
            db: Session de base de données
            student_id: ID de l'étudiant
            embedding: Vecteur d'embedding à sauvegarder
            user_id: ID de l'utilisateur
        """
        try:
            embedding_data = EmbeddingCreate(
                student_id=student_id,
                vector=embedding
            )
            
            # Vérifier si un embedding existe déjà
            existing_embedding = await get_embedding_by_student(db, student_id)
            
            if existing_embedding:
                await update_embedding(db, student_id, embedding_data)

                await db_logger.debug(
                    f"✅ Embedding facial mis à jour pour l'étudiant {student_id}",
                    "face_enrollment.embedding_updated",
                    user_id=user_id
                )
            
            else:
                await create_embedding(db, embedding_data)
                
                await db_logger.debug(
                    f"✅ Nouvel embedding facial créé pour l'étudiant {student_id}",
                    "face_enrollment.embedding_created",
                    user_id=user_id
                ) 
                               
        except Exception as e:
            await db_logger.error(
                f"❌ Erreur lors de la sauvegarde de l'embedding pour l'étudiant {student_id}: {str(e)}",
                "face_enrollment.embedding_save_error",
                user_id=user_id
            )
            raise
    
    async def _update_student_enrollment_status(
        self,
        db: AsyncSession,
        student_id: str,
        enrolled: bool
    ) -> None:
        """
        Met à jour le statut d'enrôlement facial de l'étudiant.
        
        Args:
            db: Session de base de données
            student_id: ID de l'étudiant
            enrolled: Statut d'enrôlement
        """
        await db.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(faceEnrolled=enrolled)
        )
        await db.commit()

    # def cleanup_failed_jobs(self) -> None:
    #     """
    #     Nettoie les jobs échoués pour éviter l'accumulation en mémoire.
    #     """
    #     max_age_hours = 1  # Durée maximale de conservation des jobs échoués
    #     cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
    #     jobs_to_remove = [
    #         job_id for job_id, job_data in self.processing_jobs.items()
    #         if job_data.get("completed_at") and job_data["completed_at"] < cutoff_time
    #     ]
        
    #     for job_id in jobs_to_remove:
    #         del self.processing_jobs[job_id]


# Instance globale du processeur
face_enrollment_processor = FaceEnrollmentProcessor()
