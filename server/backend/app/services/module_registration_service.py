"""
Service d'enregistrement automatique des modules
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.module import Module, ModuleStatus
from app.schemas.module import ModuleCreate
from app.services.log_service import db_logger
from app.services.module_service import create_module


async def register_module_if_not_exists(
    db: AsyncSession, 
    module_uid: int, 
    module_data: dict = None
) -> Module:
    """
    Enregistre automatiquement un module s'il n'existe pas déjà
    
    Args:
        db: Session de base de données
        module_uid: UID du module
        module_data: Données supplémentaires du module (optionnel)
        
    Returns:
        Module: Module existant ou nouvellement créé
    """
    try:
        # Vérifier si le module existe déjà
        result = await db.execute(select(Module).where(Module.uid == module_uid))
        existing_module = result.scalar_one_or_none()
        
        if existing_module:
            await db_logger.debug(
                f"Module {module_uid} déjà enregistré",
                source="module_registration",
                module_uid=module_uid
            )
            return existing_module
        
        # Créer le module automatiquement
        module_create_data = ModuleCreate(
            uid=module_uid,
            name=module_data.get('name', f'Module {module_uid}') if module_data else f'Module {module_uid}',
            description=module_data.get('description', 'Module auto-enregistré') if module_data else 'Module auto-enregistré',
            emplacement=module_data.get('emplacement', 'Non spécifié') if module_data else 'Non spécifié',
            status=ModuleStatus.online,
            faceChecked=module_data.get('faceChecked', True) if module_data else True,
            rfidChecked=module_data.get('rfidChecked', True) if module_data else True
        )
        
        new_module = await create_module(db, module_create_data)
        
        await db_logger.info(
            f"🎉 Module {module_uid} s'est authentifié avec succès",
            source="module_registration",
            module_uid=module_uid,
        )
        
        return new_module
        
    except Exception as e:
        await db_logger.error(
            f"Erreur lors de l'auto-enregistrement du module {module_uid}",
            source="module_registration",
            module_uid=module_uid,
            details={"erreur": str(e)}
        )
        raise
