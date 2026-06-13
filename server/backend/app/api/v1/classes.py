from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.models.student import Student
from app.services.log_service import db_logger
from sqlalchemy import select, distinct

router = APIRouter(tags=["classes"])

@router.get("/", response_model=List[dict])
async def get_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des classes.
    
    Returns:
        Liste des classes avec leur ID et nom
    """
    try:
        # Récupérer les classes distinctes depuis la table des étudiants
        query = select(distinct(Student.classGroup)).order_by(Student.classGroup)
        result = await db.execute(query)
        classes = result.scalars().all()
        
        # Formater la réponse
        formatted_classes = [
            {"id": class_name, "name": class_name}
            for class_name in classes
            if class_name is not None
        ]
        
        await db_logger.debug(
            f"📚 Liste des classes récupérée avec succès - {len(formatted_classes)} classe(s) trouvée(s) ✅",
            source="api_classes",
            user_id=current_user.id,
            details={"nombre_classes": len(formatted_classes)}
        )
        
        return formatted_classes
        
    except Exception as e:
        await db_logger.error(
            "Erreur lors de la récupération des classes",
            source="api_classes",
            user_id=current_user.id,
            details={"erreur": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des classes: {str(e)}"
        ) 