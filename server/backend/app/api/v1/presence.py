from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

from typing import List, Optional
from datetime import datetime, date

from app.models.user import User

from app.schemas.presence import (
    PresenceCreate,
    PresenceResponse,
    PresenceSummary,
    StudentPresenceStat
)

from app.services.presence_service import (
    get_presences,
    create_presence,
    get_daily_summary,
    get_student_presence_stats
)

from app.api.v1.deps import get_db, get_current_user

from app.services.log_service import db_logger
from app.services.export_service import ExportService

router = APIRouter(tags=["presences"])

@router.get("", response_model=List[PresenceResponse])
async def read_presences(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: Optional[str] = None,
    module_uid: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[bool] = None,
    class_group: Optional[str] = None
):
    """
    Récupère tous les enregistrements de présence avec options de filtrage.
    
    Args:
        skip: Nombre d'enregistrements à sauter
        limit: Nombre maximum d'enregistrements à retourner
        student_id: Filtrer par étudiant
        module_uid: Filtrer par module
        date_from: Filtrer par date de début
        date_to: Filtrer par date de fin
        status: Filtrer par statut de présence
        class_group: Filtrer par groupe de classe
        
    Returns:
        Liste des enregistrements de présence
    """
    try:
        await db_logger.debug(
            "Demande de liste des présences",
            source="api_presence",
            user_id=current_user.id,
            details={
                "skip": skip,
                "limit": limit,
                "student_id": student_id,
                "module_uid": module_uid,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "status": status,
                "class_group": class_group,
                "chemin": request.url.path
            }
        )
        
        # Validation des dates
        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="La date de début doit être antérieure à la date de fin"
            )
        
        # Validation du module_uid
        if module_uid is not None and module_uid < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="L'identifiant du module doit être positif"
            )
        
        presences, total = await get_presences(
            db, 
            skip=skip, 
            limit=limit, 
            student_id=student_id,
            module_uid=module_uid,
            date_from=date_from,
            date_to=date_to,
            status=status,
            class_group=class_group
        )
        

        # Convertir les objets Student en dictionnaires
        response_data = []
        for p in presences:
            # Calculer les heures d'entrée et de sortie pour chaque présence
            from app.services.presence_service import calculate_entry_exit_times
            entry_time, exit_time = await calculate_entry_exit_times(db, p)
            
            presence_dict = {
                "id": p.id,
                "student_id": p.student_id,
                "status": bool(p.status) if p.status is not None else True,  # Forcer la conversion en booléen avec une valeur par défaut
                "module_uid": p.module_uid,
                "timestamp": p.timestamp,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "student": {
                    "id": p.student.id,
                    "firstName": p.student.firstName,
                    "lastName": p.student.lastName,
                    "classGroup": p.student.classGroup
                } if p.student else None
            }
            response_data.append(PresenceResponse.model_validate(presence_dict))
        
        return response_data
    
    except ValueError as e:
        # await db_logger.error(
        #     "Erreur de validation lors de la récupération des présences",
        #     source="api_presence",
        #     user_id=current_user.id,
        #     details={
        #         "erreur": str(e),
        #         "skip": skip,
        #         "limit": limit,
        #         "student_id": student_id,
        #         "module_uid": module_uid
        #     }
        # )

        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # await db_logger.error(
        #     "Erreur lors de la récupération des présences",
        #     source="api_presence",
        #     user_id=current_user.id,
        #     details={
        #         "erreur": str(e),
        #         "skip": skip,
        #         "limit": limit,
        #         "student_id": student_id,
        #         "module_uid": module_uid
        #     }
        # )

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des présences: {str(e)}"
        )

@router.get("/summary", response_model=PresenceSummary)
async def get_daily_presence_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    target_date: Optional[date] = Query(None),
    class_group: Optional[str] = None
):
    """
    Récupère un résumé des présences pour un jour spécifique.

    Args:
        target_date: La date pour laquelle obtenir le résumé (par défaut aujourd'hui)
        class_group: Filtrer par groupe de classe
        
    Returns:
        Statistiques de résumé incluant le nombre de présents, le nombre d'absents et le pourcentage
    """
    try:
        target_date = target_date or datetime.now().date()
        
        await db_logger.debug(
            "Demande de résumé quotidien des présences",
            source="api_presence",
            user_id=current_user.id,
            details={
                "date": target_date.isoformat(),
                "classe": class_group,
                "chemin": request.url.path
            }
        )
        
        summary = await get_daily_summary(db, target_date, class_group)
        
        await db_logger.debug(
            f"Résumé quotidien des présences récupéré avec succès par {current_user.firstName} {current_user.lastName}[{current_user.email}]",
            source="api_presence",
            user_id=current_user.id
        )
        
        return summary
    
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la récupération du résumé quotidien des présences",
            source="api_presence",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "date": target_date.isoformat() if 'target_date' in locals() else None,
                "classe": class_group
            }
        )

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du résumé quotidien: {str(e)}"
        )

@router.get("/student/{student_id}/stats", response_model=StudentPresenceStat)
async def get_student_presence_stats(
    student_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StudentPresenceStat:
    """
    Obtenir les statistiques de présence pour un étudiant.
    
    Args:
        student_id: ID de l'étudiant
        date_from: Date de début optionnelle
        date_to: Date de fin optionnelle
        db: Session de base de données
        current_user: Utilisateur actuel authentifié
        
    Returns:
        Statistiques de présence pour l'étudiant
    """
    try:
        await db_logger.debug(
            f"Demande des statistiques de présence pour l'étudiant {student_id}",
            source="api_presence",
            user_id=current_user.id,
            details={
                "student_id": student_id,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None
            }
        )
        
        stats = await get_student_presence_stats(
            db,
            student_id,
            date_from,
            date_to
        )
        
        await db_logger.debug(
            f"Statistiques de présence récupérées pour l'étudiant {student_id}",
            source="api_presence",
            user_id=current_user.id
        )
        
        return stats
    
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la récupération des statistiques de présence",
            source="api_presence",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "student_id": student_id
            }
        )
        
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des statistiques de présence"
        )

@router.post("", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED)
async def create_presence_record(
    payload: PresenceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouvel enregistrement de présence.
    
    Args:
        payload: Données de présence à créer
        request: Objet de requête FastAPI
        db: Session de base de données
        current_user: Utilisateur actuel
        
    Returns:
        Enregistrement de présence créé
    """
    try:
        await db_logger.debug(
            "Demande de création d'un enregistrement de présence",
            source="api_presence",
            user_id=current_user.id,
            details={
                "étudiant_id": payload.student_id,
                "module_uid": payload.module_uid,
                "statut": payload.status,
                "chemin": request.url.path
            }
        )        
        
        # Créer la présence
        presence = await create_presence(db, payload)
        
        # Récupérer les informations de l'étudiant séparément pour éviter les problèmes de relations
        from app.services.student_service import get
        student = await get(db, presence.student_id)
        
        # Calculer les heures d'entrée et de sortie
        from app.services.presence_service import calculate_entry_exit_times
        entry_time, exit_time = await calculate_entry_exit_times(db, presence)
        
        # Convertir en réponse
        response_data = {
            "id": presence.id,
            "student_id": presence.student_id,
            "status": bool(presence.status) if presence.status is not None else True,
            "module_uid": presence.module_uid,
            "timestamp": presence.timestamp,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "student": {
                "id": student.id,
                "firstName": student.firstName,
                "lastName": student.lastName,
                "classGroup": student.classGroup
            } if student else None
        }
        
        # Logger la présence
        await db_logger.info(
            f" Présence enregistrée : Classe[{student.classGroup}] - {student.firstName} {student.lastName} - Heure d'arrivée : {entry_time}, Heure de sortie : {exit_time}.",
            source="module" if presence.module_uid else (current_user.firstName + " " + current_user.lastName),
            module_uid=presence.module_uid
        )

        return PresenceResponse.model_validate(response_data)
            
    except ValueError as e:
        await db_logger.error(
            "Erreur lors de la création de l'enregistrement de présence",
            source="api_presence",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "étudiant_id": payload.student_id,
                "module_uid": payload.module_uid
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la création de l'enregistrement de présence",
            source="api_presence",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "étudiant_id": payload.student_id,
                "module_uid": payload.module_uid
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'enregistrement de présence: {str(e)}"
        )

@router.get("/export")
async def export_presences(
    request: Request,
    target_date: date = Query(..., description="Date pour laquelle exporter les données"),
    class_group: Optional[str] = Query(None, description="Groupe de classe optionnel"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exporte les données de présence au format CSV.
    
    Args:
        target_date: Date pour laquelle exporter les données
        class_group: Groupe de classe optionnel
        
    Returns:
        Fichier CSV des présences
    """
    try:
        csv_data = await ExportService.export_presences(
            db,
            target_date,
            class_group,
            current_user.id
        )
        
        filename = f"presences_{target_date.strftime('%Y-%m-%d')}"
        if class_group:
            filename += f"_{class_group}"
        filename += ".csv"
        
        await db_logger.info(
            f"{current_user.firstName} {current_user.lastName} a téléchargé des données de présences en format csv jusqu'à la date du {target_date} de la classe {class_group}.",
            source=f"{current_user.firstName} {current_user.lastName}"
        )

        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/csv; charset=utf-8-sig"
            }
        )
        
    except Exception as e:
        await db_logger.error(
            "Erreur lors de l'export des présences",
            source="api_presence",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "date": target_date.isoformat(),
                "classe": class_group
            }
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'export des données: {str(e)}"
        )