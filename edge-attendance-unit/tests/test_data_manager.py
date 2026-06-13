"""
Tests unitaires pour le gestionnaire de données
"""

import pytest
import asyncio
import os
import json
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from datetime import datetime, timedelta

# Ajuster le chemin pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import DataManager
from schemas.schema import StudentData, APIResponse
import chromadb


class TestDataManager:
    """Tests pour la classe DataManager"""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Crée un mock du client ChromaDB"""
        client = MagicMock(spec=chromadb.Client)
        collection = MagicMock()
        client.get_or_create_collection.return_value = collection
        return client
    
    @pytest.fixture
    def mock_collection(self, mock_chroma_client):
        """Récupère le mock de collection ChromaDB"""
        return mock_chroma_client.get_or_create_collection.return_value
    
    @pytest.fixture
    def data_manager(self, monkeypatch):
        """Crée une instance de DataManager avec des mocks"""
        # Mock pour chromadb.Client
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        with patch('chromadb.Client', return_value=mock_client):
            data_manager = DataManager()
            data_manager.collection = mock_collection
            return data_manager
    
    @pytest.mark.asyncio
    async def test_fetch_students_data_success(self, data_manager, monkeypatch):
        """Teste la récupération réussie des données étudiants"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {
                "studentId": "12345",
                "first_name": "John",
                "last_name": "Doe",
                "rfidUid": "ABCDEF12",
                "faceEmbedding": [0.1, 0.2, 0.3, 0.4]
            },
            {
                "studentId": "67890",
                "first_name": "Jane",
                "last_name": "Smith",
                "rfidUid": "123456AB",
                "faceEmbedding": [0.5, 0.6, 0.7, 0.8]
            }
        ])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock pour simuler une réponse réussie avec gestion du contexte async.
        # ClientSession() et session.get() sont appelés de façon synchrone dans
        # data_manager (puis utilisés via `async with`), donc on les mocke avec
        # MagicMock ; seuls __aenter__/__aexit__ sont des AsyncMock.
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # S'assurer que last_sync_time est défini si nécessaire pour le test
        data_manager.last_sync_time = datetime.now()

        # Patch aiohttp.ClientSession (constructeur synchrone)
        monkeypatch.setattr('aiohttp.ClientSession', MagicMock(return_value=mock_session))

        # Réinitialiser le cache
        data_manager.last_sync_time = datetime.now()  # Set a datetime to avoid NoneType formatting issues
        data_manager.students_cache = {}
        data_manager.store_embeddings = MagicMock()

        result = await data_manager.fetch_students_data()

        # Vérifier les résultats
        assert len(result) == 2
        assert result[0]["studentId"] == "12345"
        assert result[1]["studentId"] == "67890"
        assert data_manager.last_sync_time is not None
        
        # Vérifier que store_embeddings a été appelé
        data_manager.store_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_students_data_api_error_with_cache(self, data_manager, monkeypatch):
        """Teste la gestion des erreurs API avec cache disponible"""
        # D'abord définir un cache
        data_manager.students_cache = [
            {
                "studentId": "12345",
                "first_name": "John",
                "last_name": "Doe",
                "rfidUid": "ABCDEF12",
                "faceEmbedding": [0.1, 0.2, 0.3, 0.4]
            }
        ]
        data_manager.last_sync_time = datetime.now()
        
        # Mock pour simuler une erreur API
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        # S'assurer que last_sync_time est défini pour éviter l'erreur de format None
        data_manager.last_sync_time = datetime.now()
        
        # Créer un mock pour aiohttp.ClientSession qui gère correctement le contexte async
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Patch directement la classe ClientSession
        monkeypatch.setattr('aiohttp.ClientSession', AsyncMock(return_value=mock_session))
        
        # Force la synchronisation mais conserve une valeur pour last_sync_time
        # pour éviter l'erreur de formatage avec None
        data_manager.last_sync_time = datetime.now() - timedelta(minutes=20)
        
        # Appel de la méthode
        result = await data_manager.fetch_students_data()
        
        # Vérifier les résultats
        assert len(result) == 1
        assert result[0]["studentId"] == "12345"
    
    @pytest.mark.asyncio
    async def test_fetch_students_data_network_error_with_cache(self, data_manager, monkeypatch):
        """Teste la gestion des erreurs réseau avec cache disponible"""
        # D'abord définir un cache
        data_manager.students_cache = [
            {
                "studentId": "12345",
                "first_name": "John",
                "last_name": "Doe",
                "rfidUid": "ABCDEF12",
                "faceEmbedding": [0.1, 0.2, 0.3, 0.4]
            }
        ]
        data_manager.last_sync_time = datetime.now()
        
        import aiohttp
        
        # S'assurer que last_sync_time est défini pour éviter l'erreur de format None
        data_manager.last_sync_time = datetime.now()
        
        # Mock pour simuler une erreur réseau
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection error"))
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Patch avec AsyncMock au lieu de MagicMock pour mieux gérer les coroutines
        monkeypatch.setattr('aiohttp.ClientSession', AsyncMock(return_value=mock_session))
        
        # Force la synchronisation mais conserve une valeur pour last_sync_time
        # pour éviter l'erreur de formatage avec None
        data_manager.last_sync_time = datetime.now() - timedelta(minutes=20)
        
        # Appel de la méthode
        result = await data_manager.fetch_students_data()
        
        # Vérifier les résultats
        assert len(result) == 1
        assert result[0]["studentId"] == "12345"
    
    def test_find_matching_student_success(self, data_manager):
        """Teste la recherche réussie d'un étudiant par embedding"""
        # Mock pour la collection
        data_manager.collection.query.return_value = {
            "distances": [[0.1]],
            "metadatas": [[{"student_id": "12345"}]]
        }
        
        # Appel de la méthode avec un embedding test
        student_id, confidence = data_manager.find_matching_student([0.1, 0.2, 0.3, 0.4], 0.8)
        
        # Vérifier les résultats
        assert student_id == "12345"
        assert confidence == 0.9  # 1.0 - 0.1 (distance cosinus)
        
        # Vérifier que query a été appelé correctement
        data_manager.collection.query.assert_called_once()
    
    def test_find_matching_student_no_match(self, data_manager):
        """Teste l'absence de correspondance lors de la recherche par embedding"""
        # Mock pour la collection (similarité sous le seuil)
        data_manager.collection.query.return_value = {
            "distances": [[0.3]],  # Distance plus grande (similarité plus faible)
            "metadatas": [[{"student_id": "12345"}]]
        }
        
        # Appel de la méthode avec un embedding test et un seuil élevé
        student_id, confidence = data_manager.find_matching_student([0.1, 0.2, 0.3, 0.4], 0.8)
        
        # Vérifier les résultats (pas de correspondance)
        assert student_id is None
        assert confidence is None
        
        # Vérifier que query a été appelé correctement
        data_manager.collection.query.assert_called_once()
    
    def test_find_matching_student_exception(self, data_manager):
        """Teste la gestion des exceptions lors de la recherche par embedding"""
        # Mock pour lever une exception
        data_manager.collection.query.side_effect = Exception("Test d'erreur")
        
        # Appel de la méthode
        student_id, confidence = data_manager.find_matching_student([0.1, 0.2, 0.3, 0.4], 0.8)
        
        # Vérifier les résultats (erreur)
        assert student_id is None
        assert confidence is None
    
    def test_get_student_by_rfid_success(self, data_manager):
        """Teste la recherche réussie d'un étudiant par RFID"""
        # Configurer le cache
        data_manager.students_cache = [
            MagicMock(studentId="12345", rfidUid="ABCDEF12"),
            MagicMock(studentId="67890", rfidUid="123456AB")
        ]
        
        # Appel de la méthode
        student_id = data_manager.get_student_by_rfid("ABCDEF12")
        
        # Vérifier le résultat
        assert student_id == "12345"
    
    def test_get_student_by_rfid_not_found(self, data_manager):
        """Teste l'absence de correspondance lors de la recherche par RFID"""
        # Configurer le cache
        data_manager.students_cache = [
            MagicMock(studentId="12345", rfidUid="ABCDEF12"),
            MagicMock(studentId="67890", rfidUid="123456AB")
        ]
        
        # Appel de la méthode avec un RFID non existant
        student_id = data_manager.get_student_by_rfid("UNKNOWN")
        
        # Vérifier le résultat (pas de correspondance)
        assert student_id is None
    
    def test_get_student_by_rfid_empty_cache(self, data_manager):
        """Teste la recherche par RFID avec un cache vide"""
        # Vider le cache
        data_manager.students_cache = {}
        
        # Appel de la méthode
        student_id = data_manager.get_student_by_rfid("ABCDEF12")
        
        # Vérifier le résultat (pas de cache)
        assert student_id is None
