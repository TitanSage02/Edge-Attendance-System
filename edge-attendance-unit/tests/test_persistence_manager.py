"""
Tests unitaires pour le gestionnaire de persistance
"""

import pytest
import asyncio
import os
import json
import shutil
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from datetime import datetime

# Ajuster le chemin pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.persistence_manager import PersistenceManager


class TestPersistenceManager:
    """Tests pour la classe PersistenceManager"""
    
    @pytest.fixture
    def test_storage_dir(self, tmp_path):
        """Crée un répertoire temporaire pour les tests"""
        test_dir = tmp_path / "test_queue"
        test_dir.mkdir()
        yield str(test_dir)
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
    
    @pytest.fixture
    def persistence_manager(self, test_storage_dir):
        """Crée une instance de PersistenceManager avec un répertoire temporaire"""
        return PersistenceManager(storage_dir=test_storage_dir)
    
    @pytest.mark.asyncio
    async def test_enqueue_and_save(self, persistence_manager, test_storage_dir):
        """Teste l'ajout d'un événement et sa sauvegarde"""
        # Données de test
        test_data = {"student_id": "12345", "status": True, "module_uid": 1}
        
        # Ajouter à la file
        result = await persistence_manager.enqueue("presence", test_data)
        
        # Vérifier les résultats
        assert result is True
        assert len(persistence_manager.queues["presence"]) == 1
        assert persistence_manager.queues["presence"][0]["student_id"] == "12345"
        
        # Vérifier que le fichier a été créé
        queue_file = os.path.join(test_storage_dir, "presence_queue.json")
        assert os.path.exists(queue_file)
        
        # Vérifier le contenu du fichier
        with open(queue_file, "r") as f:
            saved_data = json.load(f)
            assert len(saved_data) == 1
            assert saved_data[0]["student_id"] == "12345"
            assert "timestamp" in saved_data[0]
    
    @pytest.mark.asyncio
    async def test_load_persisted_data(self, test_storage_dir):
        """Teste le chargement des données persistées"""
        # Créer un fichier de données
        queue_file = os.path.join(test_storage_dir, "presence_queue.json")
        test_data = [
            {"student_id": "12345", "status": True, "module_uid": 1, "timestamp": "2023-01-01T12:00:00"},
            {"student_id": "67890", "status": True, "module_uid": 1, "timestamp": "2023-01-01T13:00:00"}
        ]
        
        with open(queue_file, "w") as f:
            json.dump(test_data, f)
        
        # Créer un nouveau gestionnaire qui devrait charger les données
        manager = PersistenceManager(storage_dir=test_storage_dir)
        await manager.initialize()
        
        # Vérifier que les données ont été chargées
        assert len(manager.queues["presence"]) == 2
        assert manager.queues["presence"][0]["student_id"] == "12345"
        assert manager.queues["presence"][1]["student_id"] == "67890"
    
    @pytest.mark.asyncio
    async def test_process_queues(self, persistence_manager):
        """Teste le traitement des files d'attente"""
        # Configurer un callback mock qui réussit toujours
        presence_callback = AsyncMock(return_value=True)
        persistence_manager.register_callback("presence", presence_callback)
        
        # Mock pour _save_queue pour éviter les erreurs de sauvegarde
        persistence_manager._save_queue = AsyncMock()
        
        # Ajouter des événements à la file
        await persistence_manager.enqueue("presence", {"student_id": "12345", "status": True})
        await persistence_manager.enqueue("presence", {"student_id": "67890", "status": True})
        
        # S'assurer que is_processing est initialement à False
        persistence_manager.is_processing = False
        
        # Déclencher le traitement
        await persistence_manager._process_queues()
        
        # Vérifier que le callback a été appelé deux fois
        assert presence_callback.call_count == 2
        # Vérifier que la file a été vidée
        assert len(persistence_manager.queues["presence"]) == 0
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self, persistence_manager):
        """Teste la gestion des erreurs lors de l'appel des callbacks"""
        # Configurer un callback qui lève une exception
        async def error_callback(data):
            raise Exception("Test error")
            
        persistence_manager.register_callback("presence", error_callback)
        
        # Ajouter un événement à la file
        await persistence_manager.enqueue("presence", {"student_id": "12345", "status": True})
        
        # Déclencher le traitement
        await persistence_manager._process_queues()
        
        # L'événement devrait toujours être dans la file car le traitement a échoué
        assert len(persistence_manager.queues["presence"]) == 1
    
    @pytest.mark.asyncio
    async def test_on_reconnection(self, persistence_manager):
        """Teste le comportement lors d'une reconnexion"""
        # Mock pour _process_queues
        persistence_manager._process_queues = AsyncMock()
        
        # Déclencher une reconnexion
        await persistence_manager.on_reconnection()
        
        # Vérifier que _process_queues a été appelé
        persistence_manager._process_queues.assert_called_once()
        # Vérifier que l'événement reconnected a été défini
        assert persistence_manager.reconnected_event.is_set()
    
    def test_get_queue_sizes(self, persistence_manager):
        """Teste la récupération des tailles de files"""
        # Configurer des files avec des données
        persistence_manager.queues["presence"] = [{"id": 1}, {"id": 2}]
        persistence_manager.queues["logs"] = [{"id": 1}]
        persistence_manager.queues["status"] = []
        
        # Obtenir les tailles
        sizes = persistence_manager.get_queue_sizes()
        
        # Vérifier les résultats
        assert sizes["presence"] == 2
        assert sizes["logs"] == 1
        assert sizes["status"] == 0
