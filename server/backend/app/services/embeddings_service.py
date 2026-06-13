from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from typing import List, Optional

from datetime import datetime

from app.models.embedding import Embedding
from app.schemas.embeddings import EmbeddingCreate

from app.services.log_service import db_logger

async def create_embedding(db: AsyncSession, embedding_data: EmbeddingCreate) -> Embedding:
    """
    Create a new face embedding for a student.
    
    Args:
        db: Database session
        embedding_data: Data for creating the embedding
        
    Returns:
        Created embedding record
    """
    
    # Create new embedding record
    db_embedding = Embedding(
        student_id=embedding_data.student_id,
        vector=embedding_data.vector,
    )
    
    db.add(db_embedding)
    
    try:
        await db.commit()
        await db.refresh(db_embedding)
        
        await db_logger.debug(
            "embedding_created",
            source="create_embedding"
        )
        
        return db_embedding
    
    except Exception as e:
        await db.rollback()
        
        await db_logger.error(
            "embedding_creation_failed",
            source="create_embedding"
        )
        raise

async def get_embedding_by_student(db: AsyncSession, student_id: str) -> Optional[Embedding]:
    """
    Get face embedding for a specific student.
    
    Args:
        db: Database session
        student_id: ID of the student
        
    Returns:
        Embedding record if found, None otherwise
    """

    query = select(Embedding).filter(Embedding.student_id == student_id)
    result = await db.execute(query)
    embedding = result.scalar_one_or_none()
    
    # Ensure the embedding is fully loaded from the database
    if embedding:
        await db.refresh(embedding)
    
    return embedding

async def get_all_embeddings(
    db: AsyncSession
) -> List[Embedding]:
    """
    Get all face embeddings with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of embedding records
    """
    query = select(Embedding).order_by(Embedding.student_id)
    result = await db.execute(query)
    
    return result.scalars().all()

async def update_embedding(
    db: AsyncSession, 
    student_id: str, 
    embedding_data: EmbeddingCreate
) -> Optional[Embedding]:
    """
    Update face embedding for a specific student.
    
    Args:
        db: Database session
        student_id: ID of the student
        embedding_data: New embedding data
        
    Returns:
        Updated embedding record if found, None otherwise
    """
    # Get current embedding
    embedding = await get_embedding_by_student(db, student_id)
    if not embedding:
        return None
        
    try:
        # Update the vector field
        embedding.vector = embedding_data.vector
        
        # Flush to ensure the object is updated in the session
        await db.flush()
        await db.commit()
        await db.refresh(embedding)
        
        await db_logger.debug(
            "embedding_updated",
            source="update_embedding"
        )
        
        return embedding
   
    except Exception as e:
        await db.rollback()

        await db_logger.error(
            "embedding_update_failed",
            source="update_embedding"
        )
        raise

async def delete_embedding(db: AsyncSession, student_id: str) -> bool:
    """
    Delete face embedding for a specific student.
    
    Args:
        db: Database session
        student_id: ID of the student
        
    Returns:
        True if embedding was deleted, False if not found
    """
    
    # Get current embedding
    embedding = await get_embedding_by_student(db, student_id)
    if not embedding:
        return False
    
    try:
        await db.delete(embedding)
        await db.commit()
        
        await db_logger.debug(
            "embedding_deleted",
            source="delete_embedding"
        )
        
        return True
    
    except Exception as e:
        await db.rollback()
        await db_logger.error(
            "embedding_deletion_failed",
            source="delete_embedding"
        )
        raise
