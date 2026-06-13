from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from datetime import datetime, date
from typing import List, Optional
import csv
import io

from app.models.presence import Presence
from app.models.student import Student
from app.services.log_service import db_logger

class ExportService:
    @staticmethod
    async def export_presences(
        db: AsyncSession,
        target_date: date,
        class_group: Optional[str] = None,
        user_id: str = None
    ) -> bytes:
        """
        Exporte les données de présence au format CSV.
        Par défaut, tous les étudiants sont considérés comme absents.
        
        Args:
            db: Session de base de données
            target_date: Date pour laquelle exporter les données
            class_group: Groupe de classe optionnel
            user_id: ID de l'utilisateur effectuant l'export
            
        Returns:
            Données CSV en bytes
        """
        try:
            # Requête pour obtenir tous les étudiants
            base_query = select(Student)
            if class_group:
                base_query = base_query.filter(Student.classGroup == class_group)
            
            # Exécuter la requête pour obtenir tous les étudiants
            students_result = await db.execute(base_query)
            all_students = students_result.scalars().all()
            
            # Requête pour obtenir les présences signalées
            presence_query = (
                select(
                    Presence.student_id,
                    Presence.status,
                    Presence.timestamp
                )
                .filter(Presence.timestamp >= datetime.combine(target_date, datetime.min.time()))
                .filter(Presence.timestamp <= datetime.combine(target_date, datetime.max.time()))
            )
            
            if class_group:
                presence_query = presence_query.join(Student).filter(Student.classGroup == class_group)
            
            presence_result = await db.execute(presence_query)
            presence_records = {record.student_id: record for record in presence_result}
            
            # Créer le fichier CSV en mémoire
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';')
            
            # Écrire l'en-tête
            writer.writerow([
                "ID Étudiant",
                "Prénom",
                "Nom",
                "Classe",
                "Statut",
                "Heure d'entrée"
            ])
            
            # Écrire les données
            for student in all_students:
                presence_record = presence_records.get(student.id)
                if presence_record:
                    # L'étudiant a signalé sa présence
                    writer.writerow([
                        student.id or "Non renseigné",
                        student.firstName or "Non renseigné",
                        student.lastName or "Non renseigné",
                        student.classGroup or "Non renseigné",
                        "Présent",  # S'il a signalé sa présence, il est considéré comme présent
                        presence_record.timestamp.strftime("%H:%M") if presence_record.timestamp else "Non renseigné"
                    ])
                else:
                    # L'étudiant n'a pas signalé sa présence, il est considéré comme absent par défaut
                    writer.writerow([
                        student.id or "Non renseigné",
                        student.firstName or "Non renseigné",
                        student.lastName or "Non renseigné",
                        student.classGroup or "Non renseigné",
                        "Absent",  # Par défaut, tous les étudiants sont absents
                        "Non renseigné"  # Pas d'heure d'entrée car pas de signalement
                    ])
            
            # Si aucun étudiant n'est trouvé, ajouter une ligne d'information
            if not all_students:
                writer.writerow([
                    "Aucun étudiant",
                    "trouvé pour",
                    "cette classe",
                    "",
                    "",
                    ""
                ])
            
            # Journaliser l'export
            await db_logger.debug(
                f"📊 Export des présences effectué avec succès pour la classe {class_group} 📈",
                source="export_service",
                user_id=user_id,
                details={
                    "date": target_date.isoformat(),
                    "classe": class_group,
                    "nombre_étudiants": len(all_students)
                }
            )
            
            return output.getvalue().encode('utf-8-sig')
            
        except Exception as e:
            await db_logger.error(
                f"❌ Erreur lors de l'export des présences pour la classe {class_group} 🚨",
                source="export_service",
                user_id=user_id,
                details={
                    "erreur": str(e),
                    "date": target_date.isoformat(),
                    "classe": class_group
                }
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de l'export des données: {str(e)}"
            )