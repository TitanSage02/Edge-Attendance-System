import datetime as dt

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.hashing import hash_password
from app.services.log_service import db_logger


class CRUDUser:
    async def get_by_email(self, db: AsyncSession, *, email: str):
        res = await db.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        
        return user
    
    async def get_by_id(self, db: AsyncSession, *, user_id: int):
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()

        return user

    async def create(self, 
                     db: AsyncSession, *, 
                     email: str, 
                     password: str,
                     role : str,
                     firstName : str,
                     lastName : str,
                     ):
        
        user = User(email=email, 
                    hashed_password=hash_password(password),
                    firstName=firstName,
                    lastName=lastName,
                    role=role
                    )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user    
    
    async def delete(self, db: AsyncSession, *, user: User):
        user_id = user.id
        email = user.email
        
        try:
            # Supprimer d'abord tous les refresh tokens associés
            from app.models.user import RefreshToken
            from sqlalchemy import delete as sql_delete
            
            # Supprimer les refresh tokens associés à cet utilisateur
            await db.execute(
                sql_delete(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            
            # Maintenant supprimer l'utilisateur
            await db.delete(user)
            await db.commit()

        except Exception as e:
            await db.rollback()      

            await db_logger.error(
                f"❌ Une erreur s'est produite lors de la suppression de l'utilisateur {email}.",
                source="utilisateurs"
            )
            raise

    async def update(self, db: AsyncSession, *, user_id: int = None, user: User = None, **kwargs):
        """
        Met à jour un utilisateur soit à partir d'un objet utilisateur, soit à partir d'un ID.
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur à mettre à jour (optionnel si user est fourni)
            user: Objet utilisateur à mettre à jour (optionnel si user_id est fourni)
            **kwargs: Champs à mettre à jour
        
        Returns:
            Utilisateur mis à jour
        
        Raises:
            ValueError: Si ni user_id ni user n'est fourni
        """
        if user is None and user_id is None:
            raise ValueError("Vous devez fournir soit un objet user, soit un user_id")
        
        if user is None:
            # Si seulement l'ID est fourni, récupérer l'utilisateur
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()            
            if not user:
                return None
        else:
            user_id = user.id
        
        # Sauvegarde des anciennes valeurs pour le logging
        # old_values = {key: getattr(user, key) for key in kwargs.keys() if hasattr(user, key)}
        
        # Mise à jour via user object ou via statement SQL selon le cas
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            
            await db.commit()
            await db.refresh(user)
        else:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**kwargs)
                .execution_options(synchronize_session="fetch")
            )
            await db.execute(stmt)
            await db.commit()
            
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one()
            
        return user

    async def increment_token_version(self, db: AsyncSession, user: User):        
        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(token_version=User.token_version + 1)
        )

        await db.commit()

crud_user = CRUDUser()