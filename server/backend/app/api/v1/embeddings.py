from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form, BackgroundTasks
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from typing import Union, List
import json
import io
import uuid
from PIL import Image
import numpy as np

from app.models.user import User
from app.models.api_key import ApiKey
from app.models.student import Student
from app.schemas.embeddings import (
    EmbeddingCreate, 
    EmbeddingRead, 
    EmbeddingOperationResponse, 
)
from app.schemas.face_enrollment import (
    FaceEnrollmentResponse,
    FaceEnrollmentBatchResponse
)
from app.services.embeddings_service import (
    create_embedding,
    get_embedding_by_student,
    update_embedding,
    delete_embedding
)
from app.services.face_enrollment_service import face_enrollment_processor
from app.services.mqtt_service import publish_mqtt_update
from app.api.v1.deps import get_db, get_current_user, get_api_key
from app.services.log_service import db_logger

router = APIRouter(tags=["embeddings"])

async def validate_student_id(db: AsyncSession, student_id: str):
    """Vérifie si l'étudiant existe dans la base de données."""
    result = await db.execute(select(Student).where(Student.id == student_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")

async def validate_embedding_vector(embedding: list):
    """Vérifie que le vecteur d'embedding contient exactement 512 flottants."""
    if not isinstance(embedding, list) or len(embedding) != 512 or not all(isinstance(x, (int, float)) for x in embedding):
        raise HTTPException(
            status_code=400,
            detail="L'embedding doit être une liste de 512 nombres flottants"
        )

@router.get("/{student_id}", response_model=EmbeddingRead)
async def read_embedding_by_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Union[User, ApiKey] = Depends(lambda x: get_current_user(x) or get_api_key(x))
):
    """
    Récupère l'embedding facial pour un étudiant spécifique.
    
    Paramètres:
    - student_id: L'ID de l'étudiant
    
    Retourne:
    - L'embedding facial de l'étudiant
    
    Lève:
    - 404: Si l'étudiant ou l'embedding n'est pas trouvé
    """
    await validate_student_id(db, student_id)
    
    db_logger.debug(
        f"🔍 Demande de l'embedding de l'étudiant {student_id} reçue avec succès.✅",
        source="embeddings_api",
        module_uid=auth.module_uid
    )

    embedding = await get_embedding_by_student(db, student_id)
    if not embedding:
        db_logger.warning(
            f"❌ Données biométriques absentes pour l'étudiant {student_id} 📊",
            source="embeddings_api",
            module_uid=auth.module_uid
        )
        raise HTTPException(status_code=404, detail="Face embedding not found for this student")
    
    return embedding

# Utiliser par les modules pour continuer par enricher les données
@router.post("/", response_model=EmbeddingRead, status_code=status.HTTP_201_CREATED)
async def create_face_embedding(
    embedding: EmbeddingCreate,
    db: AsyncSession = Depends(get_db),
    auth: Union[User, ApiKey] = Depends(lambda x: get_current_user(x) or get_api_key(x))
):
    """
    Créer un nouvel embedding facial pour un étudiant.
    
    Paramètres:
    - embedding: Données d'embedding incluant l'ID de l'étudiant et le vecteur de 128 flottants
    
    Retourne:
    - Enregistrement d'embedding créé
    """

    await validate_student_id(db, embedding.student_id)
    await validate_embedding_vector(embedding.vector)
    
    db_logger.info(
        f"✨ Nouveau embedding créé avec succès pour l'étudiant {embedding.student_id} par {auth.module_uid} 🎯",
        source="embeddings_api",
        module_uid=auth.module_uid
    )
    
    try:
        created_embedding = await create_embedding(db, embedding)
        return created_embedding
    except Exception as e:
        db_logger.error(
            f"📡 Erreur de transmission MQTT pour l'étudiant {embedding.student_id} : {str(e)} ⚠️",
            source="embeddings_api",
            module_uid=auth.module_uid
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de l'embedding: {str(e)}"
        )


@router.post("/face-enrollment/{student_id}", response_model=FaceEnrollmentResponse)
async def upload_face_enrollment_photos(
    student_id: str,
    photos: List[UploadFile] = File(..., description="6 photos d'enrôlement facial"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload et traitement des photos d'enrôlement facial en arrière-plan.
    
    Cette endpoint accepte les photos, les valide rapidement et lance
    le traitement d'extraction des embeddings en tâche de fond pour
    une réponse rapide au frontend.
    
    Args:
        student_id: ID de l'étudiant pour l'enrôlement
        photos: Liste de 6 photos d'enrôlement facial
        current_user: Utilisateur authentifié
        
    Returns:
        Réponse immédiate avec l'ID du job et l'URL de suivi
        
    Raises:
        400: Si le nombre de photos est incorrect ou validation échoue
        404: Si l'étudiant n'existe pas
    """
    
    # Validation rapide du nombre de photos
    if len(photos) != 6:
        raise HTTPException(
            status_code=400, 
            detail="Exactement 6 photos sont requises pour l'enrôlement facial"
        )
    
    # Vérification que l'étudiant existe
    await validate_student_id(db, student_id)

    # Génération d'un ID unique pour le job de traitement
    job_id = str(uuid.uuid4())
    
    await db_logger.debug(
        f"📤 Réception de 6 photos d'enrôlement pour l'étudiant {student_id} - Job {job_id} créé",
        "face_enrollment.received",
        user_id=current_user.id
    )
    
    # Validation rapide des photos et lecture des données
    photos_data = []
    for i, photo in enumerate(photos):
        try:
            # Validation du type de fichier
            if not photo.content_type or not photo.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"La photo {i + 1} doit être une image valide"
                )
            
            photo_data = await photo.read()
            
            # Contrôle de la taille de la photo (optionnel)
            # if len(photo_data) > 5 * 1024 * 1024:  # 5MB max
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"La photo {i + 1} dépasse la taille maximale de 5MB"
            #     )
            
            photos_data.append(photo_data)
            
        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture de la photo {i + 1}: {str(e)}"
            )
    
    # Lancement du traitement en arrière-plan
    await face_enrollment_processor.start_enrollment_processing(
        job_id=job_id,
        student_id=student_id,
        photos_data=photos_data,
        user_id=current_user.id
    )
    
    await db_logger.debug(
        f"🚀 Traitement d'enrôlement lancé en arrière-plan pour l'étudiant {student_id} (Job: {job_id})",
        "face_enrollment.background_started",
        user_id=current_user.id
    )
    
    return FaceEnrollmentResponse(
        student_id=student_id,
        message="Enrôlement facial lancé en arrière-plan",   
    )

