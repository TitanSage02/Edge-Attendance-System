"""
Tests unitaires pour le gestionnaire d'authentification
"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from datetime import datetime

# Ajuster le chemin pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth_manager import AuthenticationManager, AuthenticationResult
from data_manager import DataManager
from sensors.camera import CameraController
from sensors.rfid import RFIDController


class TestAuthenticationManager:
    """Tests pour la classe AuthenticationManager"""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Crée un mock de DataManager"""
        data_manager = MagicMock(spec=DataManager)
        data_manager.find_matching_student = MagicMock(return_value=("12345", 0.95))
        data_manager.get_student_by_rfid = MagicMock(return_value="12345")
        return data_manager
        
    @pytest.fixture
    def mock_camera(self):
        """Crée un mock de CameraController"""
        camera = MagicMock(spec=CameraController)
        camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        return camera
        
    @pytest.fixture
    def mock_rfid(self):
        """Crée un mock de RFIDController"""
        rfid = MagicMock(spec=RFIDController)
        rfid.read_async = AsyncMock(return_value="ABCDEF12")
        return rfid
    
    @pytest.fixture
    def auth_manager(self, mock_data_manager, mock_camera, mock_rfid):
        """Crée une instance d'AuthenticationManager avec des mocks"""
        return AuthenticationManager(mock_data_manager, mock_camera, mock_rfid)
    
    @pytest.mark.asyncio
    async def test_authenticate_student_both_success(self, auth_manager, mock_camera, mock_rfid, mock_data_manager):
        """Teste l'authentification réussie avec les deux méthodes"""
        # Configurer les mocks
        mock_camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        mock_rfid.read_async = AsyncMock(return_value="ABCDEF12")
        mock_data_manager.find_matching_student.return_value = ("12345", 0.95)
        mock_data_manager.get_student_by_rfid.return_value = "12345"
        
        # Exécuter l'authentification
        result = await auth_manager.authenticate_student()
        
        # Vérifier les résultats
        assert result.success is True
        assert result.student_id == "12345"
        assert result.method == "both"
        assert result.confidence == 0.95
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
        mock_rfid.read_async.assert_awaited_once()
        mock_data_manager.find_matching_student.assert_called_once()
        mock_data_manager.get_student_by_rfid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_student_face_only(self, auth_manager, mock_camera, mock_rfid, mock_data_manager):
        """Teste l'authentification réussie avec reconnaissance faciale uniquement"""
        # Configurer les mocks
        mock_camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        mock_rfid.read_async = AsyncMock(return_value=None)  # Pas de carte RFID
        mock_data_manager.find_matching_student.return_value = ("12345", 0.95)
        
        # Exécuter l'authentification
        result = await auth_manager.authenticate_student()
        
        # Vérifier les résultats
        assert result.success is True
        assert result.student_id == "12345"
        assert result.method == "face"
        assert result.confidence == 0.95
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
        mock_rfid.read_async.assert_awaited_once()
        mock_data_manager.find_matching_student.assert_called_once()
        mock_data_manager.get_student_by_rfid.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_student_rfid_only(self, auth_manager, mock_camera, mock_rfid, mock_data_manager):
        """Teste l'authentification réussie avec RFID uniquement"""
        # Configurer les mocks
        mock_camera.capture_and_extract = AsyncMock(return_value=None)  # Pas de visage détecté
        mock_rfid.read_async = AsyncMock(return_value="ABCDEF12")
        mock_data_manager.get_student_by_rfid.return_value = "12345"
        
        # Exécuter l'authentification
        result = await auth_manager.authenticate_student()
        
        # Vérifier les résultats
        assert result.success is True
        assert result.student_id == "12345"
        assert result.method == "rfid"
        assert result.confidence == 1.0  # RFID a une confiance de 100%
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
        mock_rfid.read_async.assert_awaited_once()
        mock_data_manager.find_matching_student.assert_not_called()
        mock_data_manager.get_student_by_rfid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_student_both_mismatch(self, auth_manager, mock_camera, mock_rfid, mock_data_manager):
        """Teste l'échec d'authentification quand face et RFID ne correspondent pas"""
        # Configurer les mocks
        mock_camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        mock_rfid.read_async = AsyncMock(return_value="ABCDEF12")
        mock_data_manager.find_matching_student.return_value = ("12345", 0.95)
        mock_data_manager.get_student_by_rfid.return_value = "67890"  # ID différent
        
        # Exécuter l'authentification
        result = await auth_manager.authenticate_student()
        
        # Vérifier les résultats
        assert result.success is False
        assert result.student_id is None
        assert "Incohérence" in result.error
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
        mock_rfid.read_async.assert_awaited_once()
        mock_data_manager.find_matching_student.assert_called_once()
        mock_data_manager.get_student_by_rfid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_student_both_fail(self, auth_manager, mock_camera, mock_rfid, mock_data_manager):
        """Teste l'échec d'authentification quand les deux méthodes échouent"""
        # Configurer les mocks
        mock_camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        mock_rfid.read_async = AsyncMock(return_value=None)
        mock_data_manager.find_matching_student.return_value = (None, None)
        
        # Exécuter l'authentification
        result = await auth_manager.authenticate_student()
        
        # Vérifier les résultats
        assert result.success is False
        assert result.student_id is None
        assert "Aucune méthode" in result.error
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
        mock_rfid.read_async.assert_awaited_once()
        mock_data_manager.find_matching_student.assert_called_once()
        mock_data_manager.get_student_by_rfid.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_student_exception(self, auth_manager, mock_camera, mock_rfid, mock_data_manager):
        """Teste la gestion des exceptions lors de l'authentification"""
        # Configurer les mocks pour lever une exception dans la tâche face
        mock_camera.capture_and_extract = AsyncMock(side_effect=Exception("Test d'erreur"))
        mock_rfid.read_async = AsyncMock(return_value=None)  # Pas de RFID non plus
        
        # Exécuter l'authentification
        result = await auth_manager.authenticate_student()
        
        # Vérifier les résultats - dans ce cas, les deux méthodes échouent
        # donc le résultat devrait être un échec avec le message "Aucune méthode"
        assert result.success is False
        assert result.student_id is None
        assert "Aucune méthode" in result.error or "Erreur" in result.error
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_process_face_recognition(self, auth_manager, mock_camera, mock_data_manager):
        """Teste le processus de reconnaissance faciale"""
        # Configurer les mocks
        mock_camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        mock_data_manager.find_matching_student.return_value = ("12345", 0.95)
        
        # Exécuter la reconnaissance faciale
        student_id, confidence = await auth_manager.process_face_recognition()
        
        # Vérifier les résultats
        assert student_id == "12345"
        assert confidence == 0.95
        
        # Vérifier les appels aux méthodes
        mock_camera.capture_and_extract.assert_awaited_once()
        mock_data_manager.find_matching_student.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_rfid_reading(self, auth_manager, mock_rfid, mock_data_manager):
        """Teste le processus de lecture RFID"""
        # Configurer les mocks
        mock_rfid.read_async = AsyncMock(return_value="ABCDEF12")
        mock_data_manager.get_student_by_rfid.return_value = "12345"
        
        # Exécuter la lecture RFID
        student_id = await auth_manager.process_rfid_reading()
        
        # Vérifier les résultats
        assert student_id == "12345"
        
        # Vérifier les appels aux méthodes
        mock_rfid.read_async.assert_awaited_once()
        mock_data_manager.get_student_by_rfid.assert_called_once()
    
    def test_validate_match(self, auth_manager):
        """Teste la validation de correspondance des IDs"""
        # Test avec IDs correspondants
        assert auth_manager.validate_match("12345", "12345") is True
        
        # Test avec IDs différents
        assert auth_manager.validate_match("12345", "67890") is False
