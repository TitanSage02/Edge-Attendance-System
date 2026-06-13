from app.core.config import settings as config
from .log_processor import LogProcessor
from .embedder import GeminiEmbedder
from .vector_store import VectorStore
from .file_watcher import FileWatcher
from .ragchatbot import RAGChatbot
from typing import List, Optional
from app.services.log_service import db_logger
import threading
import time
import os

class Chatbot:
    def __init__(self):
        if config.USE_CHATBOT:
            self.log_processor = LogProcessor(config.DB_LOG_LEVELS)
            self.embedder = GeminiEmbedder(config.CHATBOT_API_KEY, config.EMBEDDING_MODEL)
            self.vector_store = VectorStore(
                config.VECTOR_DB_PATH,
                config.VECTOR_DB_COLLECTION_NAME
            )
            self.chatbot = RAGChatbot(config.CHATBOT_API_KEY, config.CHATBOT_MODEL_NAME)
            self.file_watcher = None
            self.is_running = False
            self.is_initialized = False

    
    async def initialize(self):
        """Initialise le système RAG avec reset optionnel de la base vectorielle"""
        if config.USE_CHATBOT and not self.is_initialized:
            try:
                await db_logger.debug(
                    "Initialisation du système RAG...",
                    source="Chatbot.initialize"
                )
                
                # Reset de la base vectorielle si configuré
                if config.VECTOR_DB_RESET_ON_STARTUP:
                    await db_logger.debug(
                        "Reset de la base vectorielle au démarrage activé",
                        source="Chatbot.initialize"
                    )
                    
                    reset_success = await self.vector_store.reset_collection(
                        backup_before_reset=config.VECTOR_DB_BACKUP_BEFORE_RESET
                    )
                    
                    if reset_success:
                        await db_logger.debug(
                            "Base vectorielle réinitialisée avec succès",
                            source="Chatbot.initialize"
                        )
                    else:
                        await db_logger.error(
                            "Échec du reset de la base vectorielle",
                            source="Chatbot.initialize"
                        )
                else:
                    # Afficher les statistiques actuelles
                    stats = self.vector_store.get_collection_stats()
                    await db_logger.debug(
                        f"Base vectorielle existante conservée. Entrées: {stats.get('total_entries', 0)}",
                        source="Chatbot.initialize"
                    )
                
                # Nettoyer les anciennes sauvegardes
                backup_dir = os.path.join(config.VECTOR_DB_PATH, "..", "backups")
                await self.vector_store.cleanup_old_backups(backup_dir, max_backups=5)
                
                self.is_initialized = True
                await db_logger.info(
                    "Le chatbot a été initialisé et est prêt à l'emploi",
                    source="Chatbot.initialize"
                )
                
                self.load_knowledge_base() # Charger la base de connaissances

            except Exception as e:
                await db_logger.error(
                    f"Erreur lors de l'initialisation du système RAG: {str(e)}",
                    source="Chatbot.initialize"
                )
                self.is_initialized = False
        
    def load_knowledge_base(self):
        """Charge la base de connaissances dans le système RAG"""
        if config.USE_CHATBOT:
            try:
                # Charger les logs existants
                with open("connaissance.md", 'r') as knowledge_file:
                    knowledge_content = knowledge_file.read()
                    
                if not knowledge_content.strip():
                    db_logger.warning(
                        "Le fichier de connaissance est vide, aucune donnée à charger",
                        source="Chatbot.load_knowledge_base"
                    )
                    return

                # Ajout du contenu à la base de données vectorielle
                knowledge_base_docs = [knowledge_content]
                knowledge_base_embeddings = [self.embedder.embed_text(knowledge_content)]

                self.vector_store.add_data(knowledge_base_docs, knowledge_base_embeddings)

                db_logger.info(
                    "Base de connaissances du chatbot chargée avec succès",
                    source="Chatbot.load_knowledge_base"
                )
            except Exception as e:
                db_logger.error(
                    f"Erreur lors du chargement de la base de connaissances: {str(e)}",
                    source="Chatbot.load_knowledge_base"
                )
    

    def _process_log_line(self, line: str):
        log_entry = self.log_processor.parse_log_line(line)
        if log_entry and self.log_processor.should_process(log_entry):
            # Embed and store
            embedding = self.embedder.embed_text(f"[{log_entry.level}] {log_entry.message}")
            if embedding:
                self.vector_store.add_log_entry(log_entry, embedding)
    
    def start_monitoring(self):
        if config.USE_CHATBOT: 
            if not self.is_running:
                self.file_watcher = FileWatcher(
                    config.LOG_FILE_PATH,
                    self._process_log_line
                )
                self.file_watcher.start()
                self.is_running = True
                
                # Start cleanup thread
                cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
                cleanup_thread.start()
    
    def stop_monitoring(self):
        if config.USE_CHATBOT:
            if self.file_watcher and self.is_running:
                self.file_watcher.stop()
                self.is_running = False
    
    def _cleanup_loop(self):
        while self.is_running:
            time.sleep(3600)  # Chaque heure, onn vérifie et on enlève les logs qu'on veut pas use .. 
            self.vector_store.cleanup_old_entries(config.LOG_MONITORING_RETENTION_DAYS)

    async def query(self, question: str, level_filter: Optional[List[str]] = None) -> str:
        if config.USE_CHATBOT:
            # Get query embedding
            query_embedding = self.embedder.embed_text(question)
            if not query_embedding:
                return "Erreur lors de l'embedding de la question"
            
            # Search similar logs
            results = self.vector_store.search(
                query_embedding, 
                n_results=5,
                level_filter=level_filter
            )

            await db_logger.debug(
                f"Query: {question}, Results found: {results}",
                source="Chatbot.query"
            )
            
            if not results:
                return "Aucun log pertinent trouvé"
            
            # Extract context
            context_logs = [result["document"] for result in results]
            
            # Generate response
            return self.chatbot.generate_response(question, context_logs)
        else:
            return "Hello ! Le chatbot est désactivé pour le moment. !"
    
chatbot = Chatbot()