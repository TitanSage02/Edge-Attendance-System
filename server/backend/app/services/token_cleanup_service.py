"""
Service de nettoyage des tokens expirés
"""
import datetime
from datetime import timezone
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken
from app.services.log_service import db_logger

UTC = timezone.utc
now_utc = lambda: datetime.datetime.now(UTC)

async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Nettoie les refresh tokens expirés de la base de données.
    
    Returns:
        int: Nombre de tokens supprimés
    """
    try:
        # Supprimer les tokens expirés ou révoqués
        result = await db.execute(
            delete(RefreshToken).where(
                (RefreshToken.expires_at < now_utc()) | 
                (RefreshToken.revoked_at.is_not(None))
            )
        )
        
        deleted_count = result.rowcount
        await db.commit()
        
        if deleted_count > 0:
            await db_logger.debug(
                f"🧹 Nettoyage automatique : {deleted_count} refresh tokens expirés supprimés",
                "token_cleanup.cleanup_expired"
            )
        
        return deleted_count
        
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors du nettoyage des tokens : {str(e)}",
            "token_cleanup.cleanup_expired"
        )
        await db.rollback()
        return 0

async def cleanup_user_old_tokens(db: AsyncSession, user_id: int, keep_latest: int = 5) -> int:
    """
    Nettoie les anciens tokens d'un utilisateur en gardant seulement les plus récents.
    
    Args:
        user_id: ID de l'utilisateur
        keep_latest: Nombre de tokens récents à conserver
        
    Returns:
        int: Nombre de tokens supprimés
    """
    try:
        # Récupérer les tokens de l'utilisateur triés par date de création (plus récent en premier)
        from sqlalchemy import select, func
        
        subquery = (
            select(RefreshToken.id)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now_utc()
            )
            .order_by(RefreshToken.created_at.desc())
            .offset(keep_latest)
        )
        
        result = await db.execute(
            delete(RefreshToken).where(
                RefreshToken.id.in_(subquery)
            )
        )
        
        deleted_count = result.rowcount
        await db.commit()
        
        if deleted_count > 0:
            await db_logger.debug(
                f"🧹 Nettoyage des anciens tokens pour l'utilisateur {user_id} : {deleted_count} tokens supprimés",
                "token_cleanup.cleanup_user_old",
                user_id=user_id
            )
        
        return deleted_count
        
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors du nettoyage des tokens utilisateur {user_id} : {str(e)}",
            "token_cleanup.cleanup_user_old",
            user_id=user_id
        )
        await db.rollback()
        return 0
