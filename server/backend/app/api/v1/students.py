from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math # Ajout de math pour ceil

from app.schemas.student import (
    StudentCreate, 
    StudentRead, 
    StudentUpdate, 
    StudentOperationResponse, 
    StudentModuleRead,
    StudentsPage
)

from app.services.student_service import (
    get_all, 
    get, 
    create, 
    update, 
    remove
)

from app.models.user import User
from app.models.api_key import ApiKey

from app.api.v1.deps import get_db, get_current_user, get_api_key
from app.services.log_service import db_logger

router = APIRouter(tags=["students"])

@router.get("/", response_model=StudentsPage)
async def read_students(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    class_group: Optional[str] = Query(None, alias="classGroup") # alias pour correspondre au frontend
):
    # Si limit n'est pas spécifié, on récupère tous les étudiants
    if limit is None:
        skip = 0
        limit = None
    else:
        skip = (page - 1) * limit
    await db_logger.debug(
        "📚 Demande de liste des étudiants reçue ✅",
        source="students_api",
        user_id=current_user.id,
        details={"page": page, "limit": limit, "search": search, "class_group": class_group, "path": request.url.path}
    )
    try:
        students_items, total_items = await get_all(db, skip=skip, limit=limit, search=search, class_group=class_group)
        await db_logger.debug(
            f"📊 {len(students_items)} étudiants récupérés avec succès sur {total_items} total correspondant aux critères ✅",
            source="students_api",
            user_id=current_user.id,
            details={"count": len(students_items), "total_found": total_items}
        )
        
        return StudentsPage(
            items=students_items,
            total_items=total_items,
            page=page if limit is not None else 1,
            limit=limit if limit is not None else total_items,
        )
    
    except Exception as e:
        await db_logger.error(
            "❌ Erreur lors de la récupération de la liste des étudiants 🚨",
            source="students_api",
            user_id=current_user.id,
            details={"error": str(e), "skip": skip, "limit": limit}
        )
        raise

# Récupération des données des étudiants par les modules de scan
@router.get("/data", response_model=List[StudentModuleRead]) # api/v1/students/data
async def read_students_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    await db_logger.debug(
        "📡 Demande de données étudiants par module reçue.",
        source="modules",
        user_id=api_key.module_uid,
        details={"path": request.url.path}
    )
    
    try:
        students, _ = await get_all(db)  # get_all retourne un tuple (students, total_count)
        
        students_module = []
        for student in students:
            try:
                # Récupérer les embeddings de manière sécurisée
                face_embedding = []
                if hasattr(student, 'embeddings') and student.embeddings:
                    # student.embeddings est une liste de vecteurs
                    if isinstance(student.embeddings, list) and len(student.embeddings) > 0:
                        face_embedding = student.embeddings[0]  # Premier embedding
                
                # Récupérer le RFID de manière sécurisée  
                rfid_uid = ""
                if hasattr(student, 'rfidUid') and student.rfidUid:
                    rfid_uid = student.rfidUid
                
                students_module.append(StudentModuleRead(
                    studentId=student.id, 
                    rfidUid=rfid_uid, 
                    faceEmbedding=face_embedding,
                ))
            except Exception as e:
                # Log l'erreur mais continue avec les autres étudiants
                await db_logger.warning(
                    f"Erreur lors du traitement de l'étudiant {getattr(student, 'id', 'UNKNOWN')}: {str(e)}",
                    source="students_api",
                    user_id=api_key.module_uid
                )
                continue
        
        await db_logger.info(
            f"Le module {api_key.module_uid} a récupéré avec succès les données de {len(students_module)} étudiants",
            source="students_api",
            user_id=api_key.module_uid
        )
        
        return students_module
    
    except Exception as e:
        await db_logger.error(
            f"❌ Une erreur s'est produite lors de la récupération des données d'étudiants par les modules. Erreur : {str(e)}",
            source="students_api",
            user_id=api_key.module_uid
        )

        raise


@router.post("/", response_model=StudentOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    request: Request,
    payload: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db_logger.debug(
        "👤 Demande de création d'étudiant reçue ✅",
        source="students_api",
        user_id=current_user.id,
        details={
            "student_data": {k: v for k, v in payload.dict().items() if k != "rfidUid"},
            "path": request.url.path
        }
    )
    
    try:
        # Vérification si le matricule existe déjà
        existing_student_by_matricule = await get(db, payload.id)
        if existing_student_by_matricule:
            await db_logger.warning(
                f"⚠️ Tentative de création d'étudiant avec un matricule déjà existant: {payload.id}",
                source="students_api",
                user_id=current_user.id,
                details={"matricule": payload.id}
            )
            raise HTTPException(status_code=409, detail="Un étudiant avec ce matricule existe déjà")
        
        # Vérification si l'ID existe déjà (si fourni)
        if hasattr(payload, 'id') and payload.id:
            existing_student_by_id = await get(db, payload.id)
            if existing_student_by_id:
                await db_logger.warning(
                    f"⚠️ Tentative de création d'étudiant avec un ID déjà existant: {payload.id}",
                    source="students_api",
                    user_id=current_user.id,
                    details={"id": payload.id}
                )
                raise HTTPException(status_code=409, detail="Un étudiant avec cet ID existe déjà")
        
        result = await create(db, payload)
        await db_logger.debug(
            "🎉 L'étudiant a été créé avec succès. ",
            source="students_api",
            user_id=current_user.id,
            details={"student_id": result.id, "name": f"{result.firstName} {result.lastName}"}
        )
        
        return {"message": "L'apprenant a été créé avec succès !", "success": True}
    
    except HTTPException:
        raise
    
    except Exception as e:
        await db_logger.error(
            "❌ Échec de la création de l'étudiant 🚨",
            source="students_api",
            user_id=current_user.id,
            details={"error": str(e), "student_data": {k: v for k, v in payload.model_dump().items() if k != "rfidUid"}}
        )
        return {"message": "L'apprenant n'a pas pu être créé", "success": False}

@router.get("/{student_id}", response_model=StudentRead)
async def read_student(
    student_id: str, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db_logger.debug(
        f"🔍 Demande de récupération de l'étudiant {student_id} reçue ✅",
        source="students_api",
        user_id=current_user.id,
        details={"student_id": student_id, "path": request.url.path}
    )
    
    student = await get(db, student_id)
    if not student:
        await db_logger.warning(
            f"⚠️ Étudiant {student_id} non trouvé ou supprimé 🔍",
            source="students_api",
            user_id=current_user.id,
            details={"student_id": student_id}
        )
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")
    
    await db_logger.debug(
        f"👤 Étudiant {student_id} récupéré avec succès ✅",
        source="students_api",
        user_id=current_user.id,
        details={"student_id": student_id, "name": f"{student.firstName} {student.lastName}"}
    )
    
    return student

@router.get("/data/{student_id}", response_model=StudentModuleRead) # api/v1/students/data/{student_id}
async def read_student_by_Module(
        student_id: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        api_key: ApiKey = Depends(get_api_key), 
):
    await db_logger.debug(
        f"📡 Demande de récupération de l'étudiant {student_id} par module reçue ✅",
        source="modules",
        user_id=api_key.module_uid,
        details={"student_id": student_id, "path": request.url.path}
    )
    
    student = await get(db, student_id)
    if not student:
        await db_logger.warning(
            f"⚠️ Étudiant {student_id} non trouvé ou supprimé 🔍",
            source="modules",
            user_id=api_key.module_uid,
            details={"student_id": student_id}
        )

        raise HTTPException(status_code=404, detail="Apprenant non trouvé")
   
    await db_logger.info(
        f"📡 Les données de l'étudiant {student.firstName}{student.lastName}[Promo : {student.classGroup}] récupérées avec succès par module ✅",
        source="modules",
        user_id=api_key.module_uid,
    )
    
    data = StudentModuleRead(
            studentId=student.id, 
            rfidUid=student.rfidUid, 
            faceEmbedding=student.embeddings if student.embeddings else []
        ) 

    return data


@router.patch("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Vérification du rôle admin
    if current_user.role != "admin" and current_user.role != "pedagogical":
        await db_logger.error(
            f"🚫 Tentative non autorisée de modification de l'étudiant {student_id} par {current_user.email} 🔒",
            source="students_api",
            user_id=current_user.id
        )
        raise HTTPException(status_code=403, detail="Seuls les administrateurs peuvent modifier des étudiants")
   
    await db_logger.debug(
        f"✏️ Demande de modification de l'étudiant {student_id} reçue ✅",
        source="students_api",
        user_id=current_user.id,
        details={
            "student_id": student_id, 
            "fields": list(payload.model_dump(exclude_unset=True).keys()),
            "path": request.url.path
        }
    )
    
    student = await update(db, student_id, payload)
    if not student:
        await db_logger.warning(
            f"⚠️ Échec de la modification - étudiant {student_id} non trouvé ou supprimé 🔍",
            source="students_api",
            user_id=current_user.id,
            details={"student_id": student_id}
        )
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")
    
    await db_logger.debug(
        f"✏️ Les informations de l'étudiant {student.firstName} {student.lastName} ont été mises à jour avec succès par {current_user.firstName} {current_user.lastName}",
        source="students_api",
        user_id=current_user.id
    )
    
    return student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: str, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Vérification du rôle admin
    if current_user.role != "admin" and current_user.role != "pedagogical":
        await db_logger.error(
            f"🚫 Tentative non autorisée de suppression de l'étudiant {student_id} par {current_user.email} 🔒",
            source="students_api",
            user_id=current_user.id
        )
        raise HTTPException(status_code=403, detail="Seuls les administrateurs peuvent supprimer des étudiants")
  
    await db_logger.debug(
        f"🗑️ Demande de suppression de l'étudiant {student_id} reçue ✅",
        source="students_api",
        user_id=current_user.id,
        details={"student_id": student_id, "path": request.url.path}
    )
    
    student = await remove(db, student_id)
    if not student:
        await db_logger.warning(
            f"⚠️ Échec de la suppression - étudiant {student_id} non trouvé ou déjà supprimé 🔍",
            source="students_api",
            user_id=current_user.id,
            details={"student_id": student_id}
        )
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")
    
    await db_logger.info(
        f"L'étudiant {student.firstName} {student.lastName} ({student.promotion}) a été supprimé avec succès. ✅",
        source="students_api",
        user_id=current_user.id
    )
    
    return None