from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from typing import List, Optional

from app.models.module import Module, ModuleStatus
from app.schemas.module import ModuleCreate, ModuleUpdate

from app.services.mqtt_service import mqtt_client
from app.services.log_service import db_logger

async def get_module(db: AsyncSession, module_uid: int) -> Optional[Module]:
    """
    Get a module by its ID.
    
    Args:
        db: Database session
        module_uid: UID of the module to retrieve
        
    Returns:
        Module if found, None otherwise
    """
    try:
        query = select(Module).where(Module.uid == module_uid)
        result = await db.execute(query)
        module = result.scalar_one_or_none()
        
        if module:
            await db_logger.debug(
                f"📡 Module {module_uid} récupéré avec succès ✅",
                source="service_module",
                details={"module_uid": module_uid}
            )
        else:
            await db_logger.debug(
                f"📡 Module {module_uid} non trouvé dans la base ❓",
                source="service_module",
                details={"module_uid": module_uid}
            )
        
        return module
    except Exception as e:
        await db_logger.error(
            f"❌ Échec de récupération du module {module_uid} 🚨",
            source="service_module",
            details={"module_uid": module_uid, "erreur": str(e)}
        )
        raise

async def get_modules(db: AsyncSession, skip: Optional[int] = None, limit: Optional[int] = None) -> List[Module]:
    """
    Get all modules with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (optional)
        limit: Maximum number of records to return (optional)
        
    Returns:
        List of modules
    """
    query = select(Module)
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    result = await db.execute(query)
    
    return result.scalars().all()

async def create_module(db: AsyncSession, module_data: ModuleCreate) -> Module:
    """
    Create a new module.
    Args:
        db: Database session
        module_data: Data for creating the module
    Returns:
        Created module
    """
    try:
        # Vérifier si l'uid est None
        if module_data.uid is None:
            raise ValueError("L'UID du module est requis")

        # Vérifier si l'UID existe déjà
        existing_module_query = select(Module).where(Module.uid == module_data.uid)
        existing_result = await db.execute(existing_module_query)
        existing_module = existing_result.scalar_one_or_none()
        
        if existing_module:
            await db_logger.warning(
                f"⚠️ Tentative de création d'un module avec UID {module_data.uid} déjà existant 🔄",
                source="service_module",
                details={
                    "uid_demande": module_data.uid,
                    "module_existant": existing_module.name,
                    "nouvel_utilisateur": module_data.created_by
                }
            )
            raise ValueError(f"Un module avec l'UID {module_data.uid} existe déjà. Veuillez choisir un autre UID.")

        db_module = Module(
            uid=module_data.uid,
            name=module_data.name,
            description=module_data.description,
            emplacement=module_data.emplacement,
            created_by=module_data.created_by,
            updated_by=module_data.updated_by,
            faceChecked=module_data.faceChecked,
            rfidChecked=module_data.rfidChecked,
            status=ModuleStatus.offline  # Statut par défaut
        )
        
        db.add(db_module)
        
        await db.commit()
        await db.refresh(db_module)

        await db_logger.debug(
            f"📡 Module '{db_module.name}' créé avec succès (UID: {db_module.uid}) 🎉",
            source="service_module",
            details={
                "module_uid": db_module.uid,
                "module_name": db_module.name,
                "status": db_module.status.value,
                "created_by": db_module.created_by
            }
        )
        
        # S'abonner aux topics MQTT du nouveau module
        try:
            await mqtt_client.subscribe_to_module(db_module.uid)
        except Exception as mqtt_error:
            await db_logger.warning(
                f"⚠️ Impossible de s'abonner aux topics MQTT du module {db_module.uid}: {str(mqtt_error)} 📡",
                source="service_module",
                details={
                    "module_uid": db_module.uid,
                    "mqtt_error": str(mqtt_error)
                }
            )
        
        return db_module
    
    except ValueError as ve:
        # Ne pas faire de rollback pour les erreurs de validation
        await db_logger.warning(
            f"⚠️ Erreur de validation lors de la création du module '{module_data.name}' 📋",
            source="service_module",
            details={
                "module_name": module_data.name,
                "uid_demande": module_data.uid,
                "erreur": str(ve)
            }
        )
        raise
    
    except IntegrityError as ie:
        await db.rollback()
        await db_logger.error(
            f"❌ Erreur d'intégrité lors de la création du module '{module_data.name}' 🚨",
            source="service_module",
            details={
                "module_name": module_data.name,
                "uid_demande": module_data.uid,
                "erreur": str(ie)
            }
        )
        # Fournir un message d'erreur spécifique selon le type de contrainte
        if "UNIQUE constraint failed: modules.uid" in str(ie):
            raise ValueError(f"Un module avec l'UID {module_data.uid} existe déjà. Veuillez choisir un autre UID.")
        elif "UNIQUE constraint failed: modules.name" in str(ie):
            raise ValueError(f"Un module avec le nom '{module_data.name}' existe déjà. Veuillez choisir un autre nom.")
        else:
            raise ValueError(f"Erreur de contrainte de base de données: {str(ie)}")
    
    except Exception as e:
        await db.rollback()
        await db_logger.error(
            f"❌ Échec de création du module '{module_data.name}' 🚨",
            source="service_module",
            details={
                "module_name": module_data.name,
                "uid_demande": module_data.uid,
                "erreur": str(e),
                "type_erreur": type(e).__name__
            }
        )
        raise

async def update_module(db: AsyncSession, module_uid: int, module_data: ModuleUpdate) -> Optional[Module]:
    """
    Update an existing module.
    
    Args:
        db: Database session
        module_uid: UID of the module to update
        module_data: New data for the module
        
    Returns:
        Updated module if found, None otherwise
    """

    # Get current module
    module = await get_module(db, module_uid)
    if not module:
        return None
    
    if module.faceChecked != module_data.faceChecked:
        # Publish update to MQTT
        await mqtt_client.publish_config_update(
            update_type="facial_recognition", 
            data=module_data.faceChecked
        )

    if module.rfidChecked != module_data.rfidChecked:
        # Publish update to MQTT
        await mqtt_client.publish_config_update(
            update_type="rfid", 
            data=module_data.rfidChecked
        )

    # Update fields from non-None values in the update data
    update_data = module_data.model_dump(exclude_unset=True)
    for key, value in update_data.items(): 
        setattr(module, key, value)
        

    try:
        await db.commit()
        await db.refresh(module)
        
        await db_logger.debug(
            f"✏️ Module '{module.name}' mis à jour avec succès (UID: {module_uid}) ✅",
            source="service_module",
            module_uid=module_uid,
            module_name=module.name
        )
        
        return module
    
    except Exception as e:
        await db.rollback()
        await db_logger.error(
            f"❌ Échec de mise à jour du module {module_uid} 🚨",
            source="service_module",
            module_uid=module_uid,
            error=str(e)
        )
        raise

async def delete_module(db: AsyncSession, module_uid: int) -> bool:
    """
    Delete a module.
    
    Args:
        db: Database session
        module_uid: ID of the module to delete
        
    Returns:
        True if module was deleted, False if not found
    """
    # Get current module
    module = await get_module(db, module_uid)
    if not module:
        return False
    
    try:
        await db.delete(module)
        await db.commit()
        
        await db_logger.debug(
            f"🗑️ Module '{module.name}' supprimé avec succès (UID: {module_uid}) ✅",
            source="service_module",
            module_uid=module_uid,
            module_name=module.name
        )
        
        # Se désabonner des topics MQTT du module supprimé
        try:
            await mqtt_client.unsubscribe_from_module(module_uid)
        except Exception as mqtt_error:
            await db_logger.warning(
                f"⚠️ Impossible de se désabonner des topics MQTT du module {module_uid}: {str(mqtt_error)} 📡",
                source="service_module",
                details={
                    "module_uid": module_uid,
                    "mqtt_error": str(mqtt_error)
                }
            )
        
        return True
    
    except Exception as e:
        await db.rollback()
        
        await db_logger.error(
            f"❌ Échec de suppression du module {module_uid} 🚨",
            source="service_module",
            module_uid=module_uid,
            error=str(e)
        )
        raise