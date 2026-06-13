from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from sqlalchemy.orm import selectinload

from app.models.presence import Presence
from app.models.student import Student
from app.models.module import Module  # Assumé pour la validation
from app.schemas.presence import PresenceCreate, PresenceSummary, StudentPresenceStat
from app.schemas.dashboard import AttendanceByClassSchema
from app.services.log_service import db_logger

# Constantes pour la pagination
DEFAULT_SKIP = 0
DEFAULT_LIMIT = 100

def create_date_range(
    from_date: Optional[date] = None, 
    to_date: Optional[date] = None
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Create datetime range from date objects in UTC.
    If to_date is provided, it will be set to the end of the day.
    """
    start_datetime = None
    end_datetime = None
    
    if from_date:
        start_datetime = datetime.combine(from_date, datetime.min.time()).astimezone()
    if to_date:
        end_datetime = datetime.combine(to_date, datetime.max.time()).astimezone()
        
    return start_datetime, end_datetime

async def validate_presence_data(db: AsyncSession, presence_data: PresenceCreate) -> None:
    """
    Validate that student_id and module_uid exist in the database.
    Gère la logique d'entrée/sortie : si un étudiant passe un même module une deuxième fois
    après une entrée, avec un intervalle d'au moins 2 min, on suppose que c'est la sortie.
    
    Args:
        db: Database session
        presence_data: Data for creating the presence record
        
    Raises:
        ValueError: If student_id or module_uid is invalid
    """
    try:
        # Vérifier l'étudiant
        stmt = select(Student).filter(Student.id == presence_data.student_id)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()
        if not student:
            raise ValueError(f"Étudiant {presence_data.student_id} non trouvé")
        
        # Vérifier le module seulement si module_uid n'est pas 0 (présence manuelle)
        if presence_data.module_uid != 0:
            stmt = select(Module).filter(Module.uid == presence_data.module_uid)
            result = await db.execute(stmt)
            module = result.scalar_one_or_none()
            if not module:
                raise ValueError(f"Module {presence_data.module_uid} non trouvé")
        
        # Vérifier les présences existantes pour ce module aujourd'hui
        start_datetime, end_datetime = create_date_range(date.today(), date.today())
        stmt = select(Presence).filter(
            and_(
                Presence.student_id == presence_data.student_id,
                Presence.module_uid == presence_data.module_uid,
                Presence.timestamp.between(start_datetime, end_datetime)
            )
        ).order_by(Presence.timestamp.desc())
        
        result = await db.execute(stmt)
        existing_presences = result.scalars().all()
        
        if existing_presences:
            last_presence = existing_presences[0]
            # S'assurer que les deux timestamps sont en UTC avec timezone
            current_timestamp = presence_data.timestamp or datetime.now().astimezone()
            if last_presence.timestamp.tzinfo is None:
                last_presence_ts = last_presence.timestamp.astimezone()
            else:
                last_presence_ts = last_presence.timestamp
            
            time_diff = current_timestamp - last_presence_ts
            
            # Si moins de 2 minutes se sont écoulées depuis la dernière présence
            if time_diff.total_seconds() < 120:  # 120 secondes = 2 minutes
                raise ValueError(f"L'étudiant {presence_data.student_id} a déjà une présence enregistrée pour ce module dans les 2 dernières minutes")
            
            # Si plus de 2 minutes se sont écoulées, on considère que c'est une sortie
            # et on met à jour le statut de la dernière présence
            if last_presence.status:  # Si la dernière présence était une entrée
                last_presence.status = False  # On la marque comme sortie
                await db.commit()  # Utiliser commit au lieu de flush
                await db_logger.debug(
                    "Présence mise à jour en sortie",
                    source="service_presence",
                    details={
                        "presence_id": last_presence.id,
                        "student_id": presence_data.student_id,
                        "module_uid": presence_data.module_uid,
                        "timestamp": last_presence.timestamp.isoformat()
                    }
                )
            
    except ValueError as e:
        raise e
    
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la validation des données de présence",
            source="service_presence",
            details={
                "erreur": str(e),
                "données": presence_data.model_dump()
            }
        )
        raise ValueError(f"Erreur lors de la validation des données: {str(e)}")

async def get_presences(
    db: AsyncSession, 
    skip: int = DEFAULT_SKIP, 
    limit: int = DEFAULT_LIMIT, 
    student_id: Optional[str] = None,
    module_uid: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[bool] = None,
    class_group: Optional[str] = None
) -> Tuple[List[Presence], int]:
    """
    Retrieve presence records with various filtering options.
    Optimized version with eager loading of relationships.
    """
    try:
        # Construire la requête de base avec eager loading
        base_query = (
            select(Presence)
            .options(
                selectinload(Presence.student),
                selectinload(Presence.module)
            )
            .join(Student)
        )
        
        # Appliquer les filtres
        filters = []
        if student_id:
            filters.append(Presence.student_id == student_id)
        if module_uid:
            filters.append(Presence.module_uid == module_uid)
        if status is not None:
            filters.append(Presence.status == status)
        if class_group:
            filters.append(Student.classGroup == class_group)
        
        # Filtrage par date
        try:
            start_datetime, end_datetime = create_date_range(date_from, date_to)
            if start_datetime:
                filters.append(Presence.timestamp >= start_datetime)
            
            if end_datetime:
                filters.append(Presence.timestamp <= end_datetime)

        except Exception as e:
            await db_logger.error(
                "Erreur lors du traitement des dates",
                source="service_presence",
                details={
                    "erreur": str(e),
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None
                }
            )
            raise ValueError(f"Erreur lors du traitement des dates: {str(e)}")
        
        # Appliquer tous les filtres
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        try:
            # Requête de comptage optimisée
            count_query = select(func.count()).select_from(base_query.subquery())
            total_count = await db.scalar(count_query)
        
        except Exception as e:
            await db_logger.error(
                "Erreur lors du comptage des présences",
                source="service_presence",
                details={"erreur": str(e)}
            )
            raise ValueError(f"Erreur lors du comptage des présences: {str(e)}")
        
        try:
            # Appliquer la pagination et l'ordre
            query = base_query.order_by(Presence.timestamp.desc()).offset(skip).limit(limit)
            
            # Exécuter la requête principale
            result = await db.execute(query)
            presences = result.scalars().all()
        except Exception as e:
            await db_logger.error(
                "Erreur lors de l'exécution de la requête principale",
                source="service_presence",
                details={
                    "erreur": str(e),
                    "skip": skip,
                    "limit": limit
                }
            )
            raise ValueError(f"Erreur lors de l'exécution de la requête principale: {str(e)}")
        
        return presences, total_count
        
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la récupération des présences",
            source="service_presence",
            details={
                "erreur": str(e),
                "skip": skip,
                "limit": limit,
                "student_id": student_id,
                "module_uid": module_uid,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "status": status,
                "class_group": class_group
            }
        )
        raise

async def get_presence_by_id(db: AsyncSession, presence_id: int) -> Optional[Presence]:
    """
    Get a single presence record by ID.
    
    Args:
        db: Database session
        presence_id: ID of the presence record to retrieve
        
    Returns:
        Presence record if found, None otherwise
    """
    query = select(Presence).filter(Presence.id == presence_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_presence(db: AsyncSession, presence_data: PresenceCreate) -> Presence:
    """
    Create a new presence record.
    
    Args:
        db: Database session
        presence_data: Data for creating the presence record
        
    Returns:
        Created presence record
    """
    try:
        # Valider les relations avant de commencer la transaction
        await validate_presence_data(db, presence_data)
        
        # Utiliser l'heure actuelle si non fournie
        timestamp = presence_data.timestamp or datetime.utcnow()
        
        # Pour les présences manuelles (module_uid = 0), gérer la logique entrée/sortie
        if presence_data.module_uid == 0:
            if presence_data.status is False:  # Sortie manuelle
                # Chercher la dernière entrée manuelle de cet étudiant aujourd'hui
                start_datetime, end_datetime = create_date_range(timestamp.date(), timestamp.date())
                stmt = select(Presence).filter(
                    and_(
                        Presence.student_id == presence_data.student_id,
                        Presence.module_uid == 0,  # Présences manuelles uniquement
                        Presence.status == True,  # Entrées uniquement
                        Presence.timestamp.between(start_datetime, end_datetime)
                    )
                ).order_by(Presence.timestamp.desc())
                
                result = await db.execute(stmt)
                last_entry = result.scalar_one_or_none()
                
                if last_entry:
                    # Vérifier qu'il n'y a pas déjà une sortie pour cette entrée
                    stmt_exit = select(Presence).filter(
                        and_(
                            Presence.student_id == presence_data.student_id,
                            Presence.module_uid == 0,
                            Presence.status == False,
                            Presence.timestamp > last_entry.timestamp,
                            Presence.timestamp.between(start_datetime, end_datetime)
                        )
                    )
                    
                    result_exit = await db.execute(stmt_exit)
                    existing_exit = result_exit.scalar_one_or_none()
                    
                    if existing_exit:
                        raise ValueError("Une sortie a déjà été enregistrée pour la dernière entrée de cet étudiant")
        
        # Créer l'enregistrement de présence
        db_presence = Presence(
            student_id=presence_data.student_id,
            status=presence_data.status,
            module_uid=presence_data.module_uid,
            timestamp=timestamp
        )
        
        # Utiliser la session directement sans transaction imbriquée
        db.add(db_presence)
        await db.commit()
        await db.refresh(db_presence)
        
        await db_logger.debug(
            "Présence enregistrée",
            source="service_presence",
            details={
                "presence_id": db_presence.id,
                "student_id": presence_data.student_id,
                "module_uid": presence_data.module_uid,
                "status": presence_data.status,
                "timestamp": timestamp.isoformat()
            }
        )
        
        return db_presence
            
    except ValueError as e:
        await db.rollback()
        await db_logger.warning(
            "Échec de création de la présence - Validation",
            source="service_presence",
            details={
                "erreur": str(e),
                "données": presence_data.model_dump()
            }
        )
        raise
        
    except Exception as e:
        await db.rollback()
        await db_logger.error(
            "Échec de création de la présence",
            source="service_presence",
            details={
                "erreur": str(e),
                "données": presence_data.model_dump()
            }
        )
        raise ValueError(f"Erreur lors de la création de l'enregistrement de présence: {str(e)}")

async def get_presence_by_student(
    db: AsyncSession, 
    student_id: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Presence]:
    """
    Get presence records for a specific student with optional date filtering.
    
    Args:
        db: Database session
        student_id: ID of the student
        from_date: Optional start date for filtering
        to_date: Optional end date for filtering
        
    Returns:
        List of presence records for the student
    """
    query = select(Presence).filter(Presence.student_id == student_id)
    
    # Apply date filtering if provided
    start_datetime, end_datetime = create_date_range(from_date, to_date)
    if start_datetime:
        query = query.filter(Presence.timestamp >= start_datetime)
    if end_datetime:
        query = query.filter(Presence.timestamp <= end_datetime)
    
    # Order by timestamp (newest first)
    query = query.order_by(Presence.timestamp.desc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_daily_summary(
    db: AsyncSession,
    target_date: date,
    class_group: Optional[str] = None
) -> PresenceSummary:
    """
    Get summary statistics for presences on a specific day.
    Par défaut, tous les étudiants sont considérés comme absents.
    
    Args:
        db: Database session
        target_date: Date for which to generate summary
        class_group: Optional filter for specific class
        
    Returns:
        Summary statistics including counts and percentages
    """
    try:
        start_datetime, end_datetime = create_date_range(target_date, target_date)
        
        # Obtenir le nombre total d'étudiants
        if class_group:
            total_students_query = select(func.count(Student.id)).filter(Student.classGroup == class_group)

        else:
            total_students_query = select(func.count(Student.id))
            
        total_students_result = await db.execute(total_students_query)
        total_students = total_students_result.scalar_one()
        
        # Construire la requête pour compter les étudiants qui ont signalé leur présence
        if class_group:
            stmt = (
                select(
                    func.count(Presence.id).label("present_count")
                )
                .select_from(Student)
                .join(Presence, Student.id == Presence.student_id)
                .filter(Student.classGroup == class_group)  # SQLAlchemy will map this to class_name
                .filter(Presence.timestamp.between(start_datetime, end_datetime))
            )
        else:
            stmt = select(
                func.count(Presence.id).label("present_count")
            ).filter(Presence.timestamp.between(start_datetime, end_datetime))
        
        result = await db.execute(stmt)
        row = result.one_or_none()
        
        # Les étudiants qui ont signalé leur présence sont considérés comme présents
        present_count = row.present_count if row else 0
        # Tous les autres sont absents par défaut
        absent_count = total_students - present_count
        
        # Calculer les statistiques par classe
        by_class = {}
        if not class_group:
            class_stats_query = (
                select(
                    Student.classGroup,
                    func.count(func.distinct(Presence.student_id)).label("present_count"),
                    func.count(Student.id).label("total_students")
                )
                .select_from(Student)
                .join(Presence, Student.id == Presence.student_id, isouter=True)
                .filter(Presence.timestamp.between(start_datetime, end_datetime))
                .group_by(Student.classGroup)
            )
            
            class_stats_result = await db.execute(class_stats_query)
            for row in class_stats_result:
                if row.total_students > 0:
                    # Le pourcentage de présence est basé sur ceux qui ont signalé leur présence
                    by_class[row.classGroup] = (row.present_count / row.total_students) * 100
                else:
                    by_class[row.classGroup] = 0
        
        # Calculer le pourcentage global
        presence_percentage = (present_count / total_students * 100) if total_students > 0 else 0
        
        return PresenceSummary(
            date=target_date,
            total_students=total_students,
            present_count=present_count,
            absent_count=absent_count,
            presence_percentage=presence_percentage,
            by_class=by_class
        )
        
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la génération du résumé quotidien",
            source="service_presence",
            details={
                "erreur": str(e),
                "date": target_date.isoformat(),
                "classe": class_group
            }
        )
        raise

async def get_daily_attendance_summary_by_class(
    db: AsyncSession, 
    target_date: date
) -> List[AttendanceByClassSchema]:
    """
    Get daily attendance summary grouped by class (classGroup).
    Returns a list of {name: class_name, present: count, absent: count}.
    Par défaut, tous les étudiants sont considérés comme absents.
    """
    start_datetime, end_datetime = create_date_range(target_date, target_date)

    # Requête pour obtenir le nombre total d'étudiants par classe
    total_students_query = (
        select(
            Student.classGroup.label("class_name"),
            func.count(Student.id).label("total_students")
        )
        .group_by(Student.classGroup)
        .order_by(Student.classGroup)
    )

    # Requête pour obtenir le nombre d'étudiants qui ont signalé leur présence
    present_students_query = (
        select(
            Student.classGroup.label("class_name"),
            func.count(func.distinct(Presence.student_id)).label("present_count")
        )
        .join(Presence, Student.id == Presence.student_id)
        .filter(Presence.timestamp.between(start_datetime, end_datetime))
        .group_by(Student.classGroup)
        .order_by(Student.classGroup)
    )

    absent_students_query = ""

    # Exécuter les requêtes
    total_result = await db.execute(total_students_query)
    present_result = await db.execute(present_students_query)

    # Créer un dictionnaire des présences par classe
    present_counts = {row.class_name: row.present_count for row in present_result}

    # Construire la liste des résultats
    attendance_by_class_list = []
    for row in total_result:
        if row.class_name is None:  # Ignorer les étudiants sans classe
            continue
            
        total_students = row.total_students
        present_count = present_counts.get(row.class_name, 0)
        
        # Les absents sont le total moins les présents (TODO : non, on peut avoir pour une même personne plusieurs entrées et sorties)
        absent_count = total_students - present_count

        attendance_by_class_list.append(
            AttendanceByClassSchema(
                name=row.class_name,
                present=present_count,  # Seuls ceux qui ont signalé leur présence sont comptés comme présents
                absent=absent_count     # Tous les autres sont absents par défaut
            )
        )
    
    return attendance_by_class_list

async def save_presence(db: AsyncSession, presence_data: PresenceCreate) -> Presence:
    """
    Save a presence record from MQTT data.
    
    Args:
        db: Database session
        presence_data: Presence data (PresenceCreate object)
        
    Returns:
        Created presence record
    """
    try:
        # Validate presence data
        await validate_presence_data(db, presence_data)
        
        db_presence = Presence(
            student_id=presence_data.student_id,
            status=presence_data.status,
            module_uid=presence_data.module_uid,
            timestamp=presence_data.timestamp
        )
        
        # Ajouter et sauvegarder sans transaction explicite
        db.add(db_presence)
        await db.commit()
        await db.refresh(db_presence)
        
        await db_logger.debug(
            "Présence MQTT enregistrée",
            source="service_presence",
            details={
                "presence_id": db_presence.id,
                "student_id": presence_data.student_id,
                "module_uid": presence_data.module_uid,
                "timestamp": presence_data.timestamp.isoformat() if presence_data.timestamp else None
            }
        )
        
        # Notifier le frontend via WebSocket
        await _notify_presence_update(db_presence)
        
        return db_presence
        
    except Exception as e:
        await db.rollback()
        await db_logger.error(
            "Erreur lors de l'enregistrement de la présence MQTT",
            source="service_presence",
            details={
                "erreur": str(e),
                "données": presence_data
            }
        )
        raise


async def _notify_presence_update(presence: Presence):
    """
    Notifie le frontend d'une nouvelle présence via WebSocket
    
    Args:
        presence: Record de présence créé
    """
    try:
        from app.core.websocket_manager import ws_manager
        
        # Préparer les données pour le WebSocket
        presence_data = {
            "type": "new_presence",
            "presence_id": presence.id,
            "student_id": presence.student_id,
            "module_uid": presence.module_uid,
            "status": presence.status,
            "timestamp": presence.timestamp.isoformat(),
        }
        
        # Diffuser sur le canal presence
        await ws_manager.broadcast(presence_data, "presence")
        
        # Diffuser aussi sur le canal all pour les tableaux de bord
        dashboard_data = {
            "type": "presence_update",
            "data": presence_data
        }
        await ws_manager.broadcast(dashboard_data, "all")
        
        await db_logger.debug(
            "Notification WebSocket de présence envoyée",
            source="service_presence",
            details={
                "presence_id": presence.id,
                "student_id": presence.student_id
            }
        )
        
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la notification WebSocket de présence",
            source="service_presence",
            details={
                "presence_id": presence.id,
                "erreur": str(e)
            }
        )

async def get_student_presence_stats(
    db: AsyncSession,
    student_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> StudentPresenceStat:
    """
    Obtenir les statistiques de présence pour un étudiant.
    
    Args:
        db: Session de base de données
        student_id: ID de l'étudiant
        date_from: Date de début optionnelle
        date_to: Date de fin optionnelle
        
    Returns:
        Statistiques de présence pour l'étudiant
        
    Raises:
        ValueError: Si l'étudiant n'existe pas
    """
    try:
        # Vérifier que l'étudiant existe
        student = await db.execute(select(Student).filter(Student.id == student_id))
        if not student.scalar_one_or_none():
            raise ValueError(f"Étudiant {student_id} non trouvé")
        
        # Créer la plage de dates
        start_datetime, end_datetime = create_date_range(date_from, date_to)
        
        # Requête pour obtenir les présences de l'étudiant
        query = select(Presence).filter(Presence.student_id == student_id)
        if start_datetime:
            query = query.filter(Presence.timestamp >= start_datetime)
        if end_datetime:
            query = query.filter(Presence.timestamp <= end_datetime)
        
        result = await db.execute(query)
        presences = result.scalars().all()
        
        # Calculer les statistiques
        total_days = len(presences)
        present_days = sum(1 for p in presences if p.status)
        absent_days = total_days - present_days
        presence_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Calculer les statistiques par module
        by_module = {}
        module_query = (
            select(
                Module.name,
                func.count(Presence.id).filter(Presence.status == True).label("present_count"),
                func.count(Presence.id).label("total_count")
            )
            .select_from(Presence)
            .join(Module, Presence.module_uid == Module.uid)
            .filter(Presence.student_id == student_id)
            .group_by(Module.name)
        )
        
        if start_datetime:
            module_query = module_query.filter(Presence.timestamp >= start_datetime)
        if end_datetime:
            module_query = module_query.filter(Presence.timestamp <= end_datetime)
            
        module_result = await db.execute(module_query)
        for row in module_result:
            if row.total_count > 0:
                by_module[row.name] = (row.present_count / row.total_count) * 100
            else:
                by_module[row.name] = 0
        
        # Créer le dictionnaire des présences par date
        by_date = {p.timestamp.date(): p.status for p in presences}
        
        return StudentPresenceStat(
            student_id=student_id,
            total_days=total_days,
            present_days=present_days,
            absent_days=absent_days,
            presence_percentage=presence_percentage,
            by_module=by_module,
            by_date=by_date
        )
        
    except ValueError:
        raise
    
    except Exception as e:
        await db_logger.error(
            "Erreur lors du calcul des statistiques de présence",
            source="service_presence",
            details={
                "erreur": str(e),
                "student_id": student_id
            }
        )
        raise

async def calculate_entry_exit_times(db: AsyncSession, presence: Presence) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Calculate entry and exit times for a presence record.
    
    Args:
        db: Database session
        presence: The presence record to calculate times for
        
    Returns:
        Tuple of (entry_time, exit_time)
    """
    entry_time = None
    exit_time = None
    
    if presence.module_uid == 0:  # Présence manuelle
        if presence.status:  # Si c'est une entrée
            entry_time = presence.timestamp
            
            # Chercher la sortie correspondante
            start_datetime, end_datetime = create_date_range(presence.timestamp.date(), presence.timestamp.date())
            stmt = select(Presence).filter(
                and_(
                    Presence.student_id == presence.student_id,
                    Presence.module_uid == 0,
                    Presence.status == False,  # Sortie
                    Presence.timestamp > presence.timestamp,
                    Presence.timestamp.between(start_datetime, end_datetime)
                )
            ).order_by(Presence.timestamp.asc())
            
            result = await db.execute(stmt)
            exit_presence = result.scalar_one_or_none()
            
            if exit_presence:
                exit_time = exit_presence.timestamp
                
        else:  # Si c'est une sortie
            exit_time = presence.timestamp
            
            # Chercher l'entrée correspondante
            start_datetime, end_datetime = create_date_range(presence.timestamp.date(), presence.timestamp.date())
            stmt = select(Presence).filter(
                and_(
                    Presence.student_id == presence.student_id,
                    Presence.module_uid == 0,
                    Presence.status == True,  # Entrée
                    Presence.timestamp < presence.timestamp,
                    Presence.timestamp.between(start_datetime, end_datetime)
                )
            ).order_by(Presence.timestamp.desc())
            
            result = await db.execute(stmt)
            entry_presence = result.scalar_one_or_none()
            
            if entry_presence:
                entry_time = entry_presence.timestamp
    else:
        # Pour les modules physiques, utiliser la logique existante
        if presence.status:
            entry_time = presence.timestamp
        else:
            exit_time = presence.timestamp
    
    return entry_time, exit_time