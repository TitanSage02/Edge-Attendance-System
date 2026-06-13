import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import shutil
import os
from pathlib import Path
from app.services.log_service import db_logger

class VectorStore:
    def __init__(self, persist_directory: str, collection_name: str):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = collection_name
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(name=self.collection_name)
        except Exception:
            return self.client.create_collection(name=self.collection_name)
    
    def add_log_entry(self, log_entry, embedding: List[float]):
        doc_id = f"{log_entry.timestamp}_{hash(log_entry.raw_line)}"
        
        metadata = {
            "timestamp": log_entry.timestamp,
            "level": log_entry.level,
            "source": log_entry.source,
            "created_at": datetime.now().timestamp()
        }
        
        self.collection.add(
            embeddings=[embedding],
            documents=[f"[{log_entry.level}] {log_entry.message}"],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def add_data(self, documents: List[str], embeddings: List[List[float]]):
        if len(documents) != len(embeddings):
            raise ValueError("Documents and embeddings must have the same length")

        import uuid

        # Ajout d'un timestamp pour chaque document
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=[{"created_at": datetime.now().timestamp()}] * len(documents),
            ids=[str(uuid.uuid4()) for _ in range(len(documents))]
        )

    def search(self, query_embedding: List[float], n_results: int = 5, 
               level_filter: Optional[List[str]] = None,
               hours_back: Optional[int] = None) -> List[Dict]:
        
        where_clause = {}
        if level_filter:
            where_clause["level"] = {"$in": level_filter}
        
        if hours_back:
            cutoff_time = (datetime.now() - timedelta(hours=hours_back)).timestamp()
            where_clause["created_at"] = {"$gte": cutoff_time}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        return [{
            "document": doc,
            "metadata": meta,
            "distance": dist
        } for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0]
        )]
    
    def cleanup_old_entries(self, retention_days: int):
        cutoff_timestamp = (datetime.now() - timedelta(days=retention_days)).timestamp()
        
        try:
            old_entries = self.collection.get(
                where={"created_at": {"$lt": cutoff_timestamp}}
            )
            
            if old_entries["ids"]:
                self.collection.delete(ids=old_entries["ids"])
                print(f"Supprimé {len(old_entries['ids'])} entrées anciennes")
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
    
    def get_collection_stats(self) -> Dict:
        """Récupère les statistiques de la collection vectorielle"""
        try:
            count = self.collection.count()
            return {
                "total_entries": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {
                "total_entries": 0,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "error": str(e)
            }
    
    async def backup_collection(self, backup_dir: str) -> bool:
        """Crée une sauvegarde de la base vectorielle"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Nom de sauvegarde avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"vector_db_backup_{timestamp}"
            backup_full_path = backup_path / backup_name
            
            # Copier le répertoire de la base vectorielle
            if os.path.exists(self.persist_directory):
                shutil.copytree(self.persist_directory, backup_full_path)
                
                await db_logger.debug(
                    f"Sauvegarde de la base vectorielle créée: {backup_full_path}",
                    source="VectorStore.backup_collection"
                )
                return True
            else:
                await db_logger.warning(
                    f"Répertoire de base vectorielle non trouvé: {self.persist_directory}",
                    source="VectorStore.backup_collection"
                )
                return False
                
        except Exception as e:
            await db_logger.error(
                f"Erreur lors de la sauvegarde de la base vectorielle: {str(e)}",
                source="VectorStore.backup_collection"
            )
            return False
    
    async def reset_collection(self, backup_before_reset: bool = True) -> bool:
        """Réinitialise complètement la base vectorielle"""
        try:
            stats = self.get_collection_stats()
            
            await db_logger.debug(
                f"Début du reset de la base vectorielle. Entrées actuelles: {stats.get('total_entries', 0)}",
                source="VectorStore.reset_collection"
            )

            # Sauvegarde avant reset si demandé
            if backup_before_reset and stats.get('total_entries', 0) > 0:
                backup_success = await self.backup_collection(
                    os.path.join(self.persist_directory, "..", "backups")
                )
                if backup_success:
                    await db_logger.debug(
                        "Sauvegarde pré-reset créée avec succès",
                        source="VectorStore.reset_collection"
                    )
            
            # Supprimer la collection existante
            try:
                self.client.delete_collection(name=self.collection_name)
                await db_logger.debug(
                    f"Collection '{self.collection_name}' supprimée",
                    source="VectorStore.reset_collection"
                )
            except Exception as e:
                await db_logger.warning(
                    f"Collection '{self.collection_name}' n'existait pas ou erreur lors de la suppression: {str(e)}",
                    source="VectorStore.reset_collection"
                )
            
            # Recréer une collection vide
            self.collection = self.client.create_collection(name=self.collection_name)
            
            await db_logger.debug(
                f"Base vectorielle réinitialisée avec succès. Nouvelle collection '{self.collection_name}' créée",
                source="VectorStore.reset_collection"
            )
            
            return True
            
        except Exception as e:
            await db_logger.error(
                f"Erreur lors du reset de la base vectorielle: {str(e)}",
                source="VectorStore.reset_collection"
            )
            return False
    
    async def cleanup_old_backups(self, backup_dir: str, max_backups: int = 5) -> None:
        """Nettoie les anciennes sauvegardes pour éviter l'accumulation"""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return
            
            # Lister toutes les sauvegardes vectorielles
            backups = [d for d in backup_path.iterdir() 
                      if d.is_dir() and d.name.startswith("vector_db_backup_")]
            
            # Trier par date de création (plus récent en premier)
            backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Supprimer les sauvegardes excédentaires
            if len(backups) > max_backups:
                for backup in backups[max_backups:]:
                    shutil.rmtree(backup)
                    await db_logger.debug(
                        f"Ancienne sauvegarde supprimée: {backup.name}",
                        source="VectorStore.cleanup_old_backups"
                    )
                
        except Exception as e:
            await db_logger.error(
                f"Erreur lors du nettoyage des sauvegardes: {str(e)}",
                source="VectorStore.cleanup_old_backups"
            )