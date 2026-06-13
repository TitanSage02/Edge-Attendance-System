from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from collections import Counter
import json
import traceback
from typing import List, Optional
from app.api.v1.deps import get_db, get_current_user
from app.schemas.dashboard import (
    DashboardMetricsSchema, 
    DashboardLogSchema, 
    TodayAttendanceMetricsSchema,
    AlertMetricsSchema, 
    ModuleMetricsSchema
)
from app.services import log_service, presence_service, module_service, module_status_service
from app.services.user_service import crud_user
from app.models.user import User  
from app.services.log_service import db_logger

router = APIRouter()

# Configuration
RECENT_LOGS_LIMIT = 30
# DEFAULT_TEMPERATURE = 15.0


async def _get_recent_logs_data(db: AsyncSession) -> List[DashboardLogSchema]:
    """
    Récupère et traite les logs récents avec vérifications complètes.
    """
    try:
        await db_logger.debug(
            f"Début récupération des {RECENT_LOGS_LIMIT} logs récents",
            source="dashboard._get_recent_logs_data"
        )
        
        db_recent_logs = await log_service.get_logs(db, limit=RECENT_LOGS_LIMIT)
        
        if not db_recent_logs:
            await db_logger.warning(
                "Aucun log récent trouvé dans la base de données",
                source="dashboard._get_recent_logs_data"
            )
            return []
        
        await db_logger.debug(
            f"{len(db_recent_logs)} logs récupérés de la base de données",
            source="dashboard._get_recent_logs_data"
        )
        
        recent_logs_data = []
        
        for i, log_item in enumerate(db_recent_logs):
            try:
                # Vérifications de base
                if not log_item:
                    await db_logger.warning(
                        f"Log item {i} est None, ignoré",
                        source="dashboard._get_recent_logs_data"
                    )
                    continue
                
                # Récupération du nom d'utilisateur
                user_name = None
                if hasattr(log_item, 'user_id') and log_item.user_id:
                    try:
                        user: User = await crud_user.get_by_id(db, user_id=log_item.user_id)
                        if user:
                            if hasattr(user, 'firstName') and hasattr(user, 'lastName'):
                                first_name = user.firstName or ""
                                last_name = user.lastName or ""
                                user_name = f"{first_name} {last_name}".strip()
                                if not user_name:
                                    user_name = f"User ID: {log_item.user_id}"
                            else:
                                await db_logger.warning(
                                    f"User {log_item.user_id} n'a pas les attributs firstName/lastName",
                                    source="dashboard._get_recent_logs_data"
                                )
                                user_name = f"User ID: {log_item.user_id}"
                        else:
                            await db_logger.warning(
                                f"Utilisateur avec ID {log_item.user_id} non trouvé",
                                source="dashboard._get_recent_logs_data"
                            )
                            user_name = f"User ID: {log_item.user_id} (non trouvé)"
                    except Exception as user_error:
                        await db_logger.error(
                            f"Erreur lors de la récupération de l'utilisateur {log_item.user_id}: {str(user_error)}",
                            source="dashboard._get_recent_logs_data"
                        )
                        user_name = f"User ID: {log_item.user_id} (erreur)"
                
                # Récupération du nom de module
                module_name = None
                if hasattr(log_item, 'module_uid') and log_item.module_uid:
                    try:
                        module_uid = int(log_item.module_uid)
                        module = await module_service.get_module(db, module_uid)
                        if module:
                            module_name = module.name if hasattr(module, 'name') else f"Module {module.uid}"
                        else:
                            module_name = f"Module {module_uid} (introuvable)"
                    except ValueError:
                        await db_logger.warning(
                            f"module_uid invalide dans le log: {log_item.module_uid}",
                            source="dashboard._get_recent_logs_data"
                        )
                        module_name = f"Module invalide: {log_item.module_uid}"
                    except Exception as module_error:
                        await db_logger.error(
                            f"Erreur lors de la récupération du module {log_item.module_uid}: {str(module_error)}",
                            source="dashboard._get_recent_logs_data"
                        )
                        module_name = f"Module {log_item.module_uid} (erreur)"

                # Vérifications des champs obligatoires
                log_id = getattr(log_item, 'id', None)
                timestamp = getattr(log_item, 'timestamp', None)
                level = getattr(log_item, 'level', 'INFO')
                message = getattr(log_item, 'message', 'Message non disponible')
                details = getattr(log_item, 'details', None)
                
                if log_id is None:
                    await db_logger.warning(
                        f"Log item {i} n'a pas d'ID, utilisation de l'index",
                        source="dashboard._get_recent_logs_data"
                    )
                    log_id = i
                
                if timestamp is None:
                    await db_logger.warning(
                        f"Log item {i} n'a pas de timestamp",
                        source="dashboard._get_recent_logs_data"
                    )
                
                recent_logs_data.append(
                    DashboardLogSchema(
                        id=log_id,
                        timestamp=timestamp,
                        level=level,
                        action=message,
                        details=details,
                        userName=user_name,
                        moduleName=module_name
                    )
                )
                
            except Exception as log_error:
                await db_logger.error(
                    f"Erreur lors du traitement du log item {i}: {str(log_error)}",
                    source="dashboard._get_recent_logs_data",
                    details=traceback.format_exc()
                )
                continue
        
        await db_logger.debug(
            f"{len(recent_logs_data)} logs traités avec succès",
            source="dashboard._get_recent_logs_data"
        )

        return recent_logs_data

    except Exception as e:
        await db_logger.error(
            f"Erreur critique lors de la récupération des logs récents: {str(e)}",
            source="dashboard._get_recent_logs_data",
            details=traceback.format_exc()
        )
        return []


async def _get_today_attendance_data(db: AsyncSession) -> TodayAttendanceMetricsSchema:
    """
    Récupère et traite les données de présence du jour avec vérifications complètes.
    """
    try:
        today = date.today()
        await db_logger.debug(
            f"Récupération des données de présence pour le {today}",
            source="dashboard._get_today_attendance_data"
        )
        
        by_class_summary = await presence_service.get_daily_attendance_summary_by_class(
            db, target_date=today
        )
        
        if not by_class_summary:
            await db_logger.warning(
                f"Aucune donnée de présence trouvée pour le {today}",
                source="dashboard._get_today_attendance_data"
            )
            return TodayAttendanceMetricsSchema(total=0, by_class=[])
        
        await db_logger.debug(
            f"{len(by_class_summary)} classes trouvées avec des données de présence",
            source="dashboard._get_today_attendance_data"
        )
        
        # Calculs avec vérifications
        total_present = 0
        total_absent = 0
        
        for i, item in enumerate(by_class_summary):
            try:
                present_count = getattr(item, 'present', 0)
                absent_count = getattr(item, 'absent', 0)
                
                if not isinstance(present_count, int) or present_count < 0:
                    await db_logger.warning(
                        f"Valeur présent invalide pour la classe {i}: {present_count}, utilisation de 0",
                        source="dashboard._get_today_attendance_data"
                    )
                    present_count = 0
                
                if not isinstance(absent_count, int) or absent_count < 0:
                    await db_logger.warning(
                        f"Valeur absent invalide pour la classe {i}: {absent_count}, utilisation de 0",
                        source="dashboard._get_today_attendance_data"
                    )
                    absent_count = 0
                
                total_present += present_count
                total_absent += absent_count
                
            except Exception as class_error:
                await db_logger.error(
                    f"Erreur lors du traitement des données de la classe {i}: {str(class_error)}",
                    source="dashboard._get_today_attendance_data"
                )
                continue
        
        total_records = total_present + total_absent
        
        await db_logger.debug(
            f"Résumé présence: {total_present} présents, {total_absent} absents, {total_records} total",
            source="dashboard._get_today_attendance_data"
        )
        
        return TodayAttendanceMetricsSchema(
            total=total_records,
            by_class=by_class_summary
        )
        
    except Exception as e:
        await db_logger.error(
            f"Erreur critique lors de la récupération des données de présence: {str(e)}",
            source="dashboard._get_today_attendance_data",
            details=traceback.format_exc()
        )
        return TodayAttendanceMetricsSchema(total=0, by_class=[])


async def _get_alerts_data(db: AsyncSession) -> AlertMetricsSchema:
    """
    Récupère et traite les données d'alertes avec vérifications complètes.
    """
    try:
        await db_logger.debug(
            "Récupération du nombre d'alertes critiques",
            source="dashboard._get_alerts_data"
        )
        
        critical_alerts_count = await log_service.count_logs_by_level(db, level="CRITICAL")
        
        if not isinstance(critical_alerts_count, int) or critical_alerts_count < 0:
            await db_logger.warning(
                f"Nombre d'alertes critiques invalide: {critical_alerts_count}, utilisation de 0",
                source="dashboard._get_alerts_data"
            )
            critical_alerts_count = 0
        
        await db_logger.debug(
            f"{critical_alerts_count} alertes critiques trouvées",
            source="dashboard._get_alerts_data"
        )
        
        return AlertMetricsSchema(total=critical_alerts_count)
        
    except Exception as e:
        await db_logger.error(
            f"Erreur critique lors de la récupération des alertes: {str(e)}",
            source="dashboard._get_alerts_data",
            details=traceback.format_exc()
        )
        return AlertMetricsSchema(total=0)


async def _get_modules_data(db: AsyncSession) -> ModuleMetricsSchema:
    """
    Récupère et traite les données de modules avec vérifications complètes.
    """
    try:
        await db_logger.debug(
            "Récupération des données de modules",
            source="dashboard._get_modules_data"
        )
        
        # Récupération de tous les modules
        all_modules = await module_service.get_modules(db, skip=None, limit=None)
        
        if not all_modules:
            await db_logger.warning(
                "Aucun module trouvé dans la base de données",
                source="dashboard._get_modules_data"
            )
            total_modules_count = 0
        else:
            total_modules_count = len(all_modules)
            await db_logger.debug(
                f"{total_modules_count} modules trouvés au total",
                source="dashboard._get_modules_data"
            )
        
        # Récupération des statuts de modules
        module_statuses = await module_status_service.get_module_statuses(db)
        
        if not module_statuses:
            await db_logger.warning(
                "Aucun statut de module trouvé",
                source="dashboard._get_modules_data"
            )

            return ModuleMetricsSchema(
                total=total_modules_count,
                online=0,
                offline=0,
                standby=0
            )
        
        await db_logger.debug(
            f"{len(module_statuses)} statuts de modules trouvés",
            source="dashboard._get_modules_data"
        )
        
        # Comptage des statuts avec vérifications
        status_list = []
        for i, status in enumerate(module_statuses):
            try:
                if hasattr(status, 'status') and status.status:
                    status_value = str(status.status).upper().strip()
                    status_list.append(status_value)
                else:
                    await db_logger.warning(
                        f"Statut de module {i} n'a pas de valeur valide",
                        source="dashboard._get_modules_data"
                    )
                    await db_logger.warning(
                        f"Statut de module {i} n'a pas d'attribut status valide",
                        source="dashboard._get_modules_data"
                    )

            except Exception as status_error:
                await db_logger.error(
                    f"Erreur lors du traitement du statut de module {i}: {str(status_error)}",
                    source="dashboard._get_modules_data"
                )
                continue
        
        status_counts = Counter(status_list)
        
        online_modules = max(0, status_counts.get("ONLINE", 0))
        offline_modules = max(0, status_counts.get("OFFLINE", 0))
        warning_modules = max(0, status_counts.get("WARNING", 0))
        error_modules = max(0, status_counts.get("ERROR", 0))
        standby_modules = max(0, status_counts.get("STANDBY", 0))
        
        # Ajout des modules ERROR aux WARNING
        warning_modules += error_modules
        
        await db_logger.debug(
            f"Répartition des modules: {online_modules} en ligne, {offline_modules} hors ligne, "
            f"{warning_modules} en avertissement, {standby_modules} en veille",
            source="dashboard._get_modules_data"
        )
        
        # Vérification de cohérence
        total_status_count = online_modules + offline_modules + warning_modules + standby_modules
        if total_status_count != len(status_list):
            await db_logger.warning(
                f"Incohérence dans le comptage des statuts: {total_status_count} comptés vs {len(status_list)} traités",
                source="dashboard._get_modules_data"
            )
        
        return ModuleMetricsSchema(
            total=total_modules_count,
            online=online_modules,
            offline=offline_modules,
            standby=standby_modules
        )
        
    except Exception as e:
        await db_logger.error(
            f"Erreur critique lors de la récupération des données de modules: {str(e)}",
            source="dashboard._get_modules_data",
            details=traceback.format_exc()
        )
        return ModuleMetricsSchema(
            total=0,
            online=0,
            offline=0,
            standby=0
        )


@router.get("/metrics", response_model=DashboardMetricsSchema)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les métriques pour le dashboard avec gestion complète des erreurs.
    """
    try:
        await db_logger.debug(
            f"Début récupération des métriques du dashboard pour l'utilisateur {current_user.firstName} {current_user.lastName} {current_user.email}",
            source="dashboard.get_dashboard_metrics"
        )
        
        # Vérifications préliminaires
        if not db:
            await db_logger.error(
                "Session de base de données non disponible",
                source="dashboard.get_dashboard_metrics"
            )
            raise HTTPException(status_code=500, detail="Erreur de base de données")
        
        
        # Récupération des différentes métriques
        await db_logger.debug(
            "Récupération des logs récents...",
            source="dashboard.get_dashboard_metrics"
        )
        recent_logs_data = await _get_recent_logs_data(db)
        
        await db_logger.debug(
            "Récupération des données de présence...",
            source="dashboard.get_dashboard_metrics"
        )
        today_attendance_data = await _get_today_attendance_data(db)
        
        await db_logger.debug(
            "Récupération des alertes...",
            source="dashboard.get_dashboard_metrics"
        )
        alerts_data = await _get_alerts_data(db)
        
        await db_logger.debug(
            "Récupération des données de modules...",
            source="dashboard.get_dashboard_metrics"
        )
        modules_data = await _get_modules_data(db)
        
        # Construction de la réponse finale
        dashboard_metrics = DashboardMetricsSchema(
            todayAttendance=today_attendance_data,
            alerts=alerts_data,
            modules=modules_data,
            recentLogs=recent_logs_data
        )
        
        await db_logger.debug(
            f"Métriques du dashboard récupérées avec succès: "
            f"{len(recent_logs_data)} logs, "
            f"{alerts_data.total} alertes, "
            f"{modules_data.total} modules",
            source="dashboard.get_dashboard_metrics"
        )
        
        return dashboard_metrics
        
    except HTTPException:
        # Re-raise HTTPException sans modification
        raise
        
    except Exception as e:
        error_msg = f"Erreur critique lors de la récupération des métriques du dashboard: {str(e)}"
        await db_logger.error(
            error_msg,
            source="dashboard.get_dashboard_metrics",
            details=traceback.format_exc()
        )
        
        # En cas d'erreur critique, retourner des données par défaut
        try:
            default_response = DashboardMetricsSchema(
                todayAttendance=TodayAttendanceMetricsSchema(total=0, by_class=[]),
                alerts=AlertMetricsSchema(total=0),
                modules=ModuleMetricsSchema(total=0, online=0, offline=0, standby=0),
                recentLogs=[]
            )
            
            await db_logger.warning(
                "Retour de données par défaut suite à l'erreur critique",
                source="dashboard.get_dashboard_metrics"
            )
            
            return default_response
            
        except Exception as fallback_error:
            await db_logger.critical(
                f"Impossible de créer même une réponse par défaut: {str(fallback_error)}",
                source="dashboard.get_dashboard_metrics"
            )
            raise HTTPException(
                status_code=500, 
                detail="Erreur critique du serveur"
            )