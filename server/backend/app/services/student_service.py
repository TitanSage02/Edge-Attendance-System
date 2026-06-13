from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional, Tuple

from app.models.student import Student
from app.schemas.student import StudentBase, StudentUpdate
from app.utils.sanitization import sanitize_string
from app.services.log_service import db_logger

async def get_all(
    db: AsyncSession, 
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    class_group: Optional[str] = None
) -> Tuple[List[Student], int]:
    """
    Récupère tous les étudiants avec pagination, recherche et filtres.
    Retourne aussi le nombre total d'items correspondant aux filtres.
    
    Args:
        db: Session de base de données
        skip: Nombre d'enregistrements à sauter
        limit: Nombre maximum d'enregistrements à retourner
        search: Terme de recherche (sur id, firstName, lastName)
        class_group: Filtre par groupe de classe
        
    Returns:
        Tuple (Liste des enregistrements d'étudiants, Nombre total d'étudiants filtrés)
    """
    try:
        base_query = select(Student)
        count_query = select(func.count()).select_from(Student)
        
        if search:
            search_term = f"%{search.lower()}%"
            search_filter = or_(
                Student.id.ilike(search_term),
                Student.firstName.ilike(search_term),
                Student.lastName.ilike(search_term)
            )
            base_query = base_query.filter(search_filter)
            count_query = count_query.filter(search_filter)
        if class_group:
            base_query = base_query.filter(Student.classGroup == class_group)
            count_query = count_query.filter(Student.classGroup == class_group)
        
        total_items_result = await db.execute(count_query)
        total_items = total_items_result.scalar_one_or_none() or 0
            
        query = base_query.order_by(Student.lastName, Student.firstName).offset(skip).limit(limit)
        
        # Charger les relations embeddings de manière eager
        from sqlalchemy.orm import selectinload
        query = query.options(selectinload(Student._embeddings))
        
        result = await db.execute(query)
        students = result.scalars().all()
        
        return students, total_items
    
    except Exception as e:
        await db_logger.error(
            "Échec de récupération des étudiants",
            source="service_etudiant",
            details={"erreur": str(e), "skip": skip, "limit": limit}
        )
        raise

async def get(db: AsyncSession, student_id: str) -> Optional[Student]:
    """
    Récupère un étudiant par son ID.
    
    Args:
        db: Session de base de données
        student_id: ID de l'étudiant à récupérer
        
    Returns:
        Enregistrement de l'étudiant si trouvé, None sinon
    """
    try:
        student : Student | None = await db.get(Student, student_id)
        
        if student:
            await db_logger.debug(
                f"Étudiant {student_id} récupéré",
                source="service_etudiant",
            )
        else:
            await db_logger.debug(
                f"Étudiant {student_id} non trouvé",
                source="service_etudiant",
            )
            
        return student
    except Exception as e:
        await db_logger.error(
            f"Échec de récupération de l'étudiant {student_id}",
            source="service_etudiant",
            details={"erreur": str(e), "student_id": student_id}
        )
        raise

async def create(db: AsyncSession, obj_in: StudentBase) -> Student:
    """
    Crée un nouvel étudiant.
    
    Args:
        db: Session de base de données
        obj_in: Données pour la création de l'étudiant
        
    Returns:
        Enregistrement de l'étudiant créé
    """
    try:
        # Assainir les données d'entrée
        sanitized_id = sanitize_string(obj_in.id) if obj_in.id else None
        sanitized_first_name = sanitize_string(obj_in.firstName)
        sanitized_last_name = sanitize_string(obj_in.lastName)
        sanitized_rfid = sanitize_string(obj_in.rfidUid) if obj_in.rfidUid else None
        sanitized_class = sanitize_string(obj_in.classGroup)
        sanitized_promotion = sanitize_string(obj_in.promotion)
        
        # Créer l'objet Student        
        obj = Student(
            id=sanitized_id,
            firstName=sanitized_first_name,
            lastName=sanitized_last_name,
            classGroup=sanitized_class,
            promotion=sanitized_promotion,
            faceEnrolled=obj_in.faceEnrolled,
            rfidEnrolled=obj_in.rfidEnrolled,
        )
        
        # Définir le rfidUid après la création de l'objet
        if sanitized_rfid:
            obj.rfidUid = sanitized_rfid
            
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        
        await db_logger.debug(
            "Étudiant créé",
            source="service_etudiant",
            details={
                "student_id": obj.id,
                "nom": f"{obj.firstName} {obj.lastName}",
                "classe": obj.classGroup,
                "promotion": obj.promotion
            }
        )
        
        return obj
    
    except Exception as e:
        await db.rollback()
      
        await db_logger.error(
            "Échec de création de l'étudiant",
            source="service_etudiant",
            details={
                "erreur": str(e),
                "données": obj_in.model_dump(exclude_none=True) if hasattr(obj_in, "model_dump") else vars(obj_in)
            }
        )
        raise

async def update(db: AsyncSession, student_id: str, obj_in: StudentUpdate) -> Optional[Student]:
    """
    Met à jour les informations d'un étudiant.
    
    Args:
        db: Session de base de données
        student_id: ID de l'étudiant à mettre à jour
        obj_in: Nouvelles données pour l'étudiant
        
    Returns:
        Enregistrement de l'étudiant mis à jour si trouvé, None sinon
    """
    try:
        db_obj = await get(db, student_id)
        if not db_obj:
            await db_logger.warning(
                f"Tentative de mise à jour d'un étudiant inexistant {student_id}",
                source="service_etudiant",
                details={"student_id": student_id}
            )
            return None
        
        # Obtenir les données de mise à jour et assainir les chaînes
        update_data = obj_in.model_dump(exclude_unset=True)
        if "firstName" in update_data:
            update_data["firstName"] = sanitize_string(update_data["firstName"])
        
        if "lastName" in update_data:
            update_data["lastName"] = sanitize_string(update_data["lastName"])
        
        if "classGroup" in update_data:
            update_data["classGroup"] = sanitize_string(update_data["classGroup"])
        
        # Mise à jour des champs
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        
        await db.commit()
        await db.refresh(db_obj)

        return db_obj
    
    except Exception as e:
        await db.rollback()
        
        await db_logger.error(
            f"Échec de mise à jour de l'étudiant {student_id}",
            source="service_etudiant",
            details={
                "student_id": student_id,
                "erreur": str(e),
                "données": obj_in.dict(exclude_unset=True, exclude_none=True) if hasattr(obj_in, "dict") else obj_in.model_dump(exclude_unset=True, exclude_none=True)
            }
        )
        raise

async def remove(db: AsyncSession, student_id: str) -> Optional[Student]:
    """
    Supprime un étudiant.
    
    Args:
        db: Session de base de données
        student_id: ID de l'étudiant à supprimer
        
    Returns:
        L'enregistrement de l'étudiant supprimé si trouvé, None sinon
    """
    try:
        obj = await get(db, student_id)
        
        if not obj:
            return None
        else : 
            await db.delete(obj)
            await db.commit()
            
            await db_logger.debug(
                f"Étudiant {student_id} supprimé avec succès",
                source="service_etudiant",
                details={"student_id": student_id}
            )
            
        return obj
    
    except Exception as e:
        await db.rollback()
        await db_logger.error(
            f"Échec de suppression de l'étudiant {student_id}",
            source="service_etudiant",
            details={
                "student_id": student_id,
                "erreur": str(e)
            }
        )
        raise