"""
Tests d'intégration pour le système d'authentification
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Ajuster le chemin pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth_manager import AuthenticationManager, AuthenticationResult
from data_manager import DataManager
from communication.mqtt_manager import MQTTManager
from sensors.camera import CameraController
from sensors.rfid import RFIDController
from main import AttendanceSystem

class TestAttendanceSystemIntegration:
    """Tests d'intégration pour le système de présence"""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Crée un mock de DataManager"""
        data_manager = MagicMock(spec=DataManager)
        data_manager.find_matching_student = MagicMock(return_value=("12345", 0.95))
        data_manager.get_student_by_rfid = MagicMock(return_value="12345")
        data_manager.fetch_students_data = AsyncMock(return_value=[
            {
                "studentId": "12345",
                "first_name": "John",
                "last_name": "Doe",
                "rfidUid": "ABCDEF12",
                "faceEmbedding": [0.1, 0.2, 0.3, 0.4]
            }
        ])
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
    def mock_auth_manager(self, mock_data_manager, mock_camera, mock_rfid):
        """Crée un mock d'AuthenticationManager"""
        auth_manager = MagicMock(spec=AuthenticationManager)
        auth_result = AuthenticationResult(
            success=True,
            student_id="12345",
            method="both",
            timestamp=datetime.now(),
            confidence=0.95
        )
        auth_manager.authenticate_student = AsyncMock(return_value=auth_result)
        return auth_manager
    
    @pytest.fixture
    def mock_mqtt_manager(self):
        """Crée un mock de MQTTManager"""
        mqtt_manager = MagicMock(spec=MQTTManager)
        mqtt_manager.connect = AsyncMock(return_value=True)
        mqtt_manager.publish_presence = AsyncMock(return_value=True)
        mqtt_manager.publish_status = AsyncMock(return_value=True)
        mqtt_manager.publish_log = AsyncMock(return_value=True)
        mqtt_manager.disconnect = AsyncMock(return_value=True)
        mqtt_manager.connected = asyncio.Event()
        mqtt_manager.connected.set()  # Simuler une connexion établie
        return mqtt_manager
    
    @pytest.fixture
    def mock_feedback(self):
        """Crée un mock de FeedbackController"""
        feedback = MagicMock()
        feedback.play_pattern = AsyncMock()
        feedback.indicate_success = AsyncMock()
        return feedback
    
    @pytest.fixture
    def mock_sensor(self):
        """Crée un mock de VL065XController"""
        sensor = MagicMock()
        sensor.start_monitoring = AsyncMock()
        sensor.stop_monitoring = AsyncMock()
        return sensor
    
    @pytest.fixture
    def attendance_system(self, mock_data_manager, mock_camera, mock_rfid, mock_mqtt_manager, mock_auth_manager, mock_feedback, mock_sensor):
        """Crée une instance d'AttendanceSystem avec des mocks"""
        with patch('main.DataManager', return_value=mock_data_manager), \
             patch('main.CameraController', return_value=mock_camera), \
             patch('main.RFIDController', return_value=mock_rfid), \
             patch('main.MQTTManager', return_value=mock_mqtt_manager), \
             patch('main.AuthenticationManager', return_value=mock_auth_manager), \
             patch('main.FeedbackController', return_value=mock_feedback), \
             patch('main.VL065XController', return_value=mock_sensor):
            
            system = AttendanceSystem()
            system.data_manager = mock_data_manager
            system.camera_controller = mock_camera
            system.rfid_controller = mock_rfid
            system.mqtt_manager = mock_mqtt_manager
            system.auth_manager = mock_auth_manager
            system.feedback_controller = mock_feedback
            system.sensor_controller = mock_sensor
            
            system.startup_time = datetime.now().timestamp()
            
            return system
    
    @pytest.mark.asyncio
    async def test_initialize(self, attendance_system, mock_mqtt_manager, mock_data_manager):
        """Teste l'initialisation du système"""
        # Exécuter l'initialisation
        result = await attendance_system.initialize()
        
        # Vérifier les résultats
        assert result is True
        
        # Vérifier les appels aux méthodes
        mock_mqtt_manager.connect.assert_awaited_once()
        mock_data_manager.fetch_students_data.assert_awaited_once()
        mock_mqtt_manager.publish_status.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_presence_detection(self, attendance_system, mock_auth_manager, mock_mqtt_manager, mock_feedback):
        """Teste la détection de présence et l'authentification"""
        # Simuler une détection de présence
        await attendance_system._on_presence_detected()
        
        # Vérifier les appels aux méthodes
        mock_auth_manager.authenticate_student.assert_awaited_once()
        mock_feedback.indicate_success.assert_awaited_once()
        mock_mqtt_manager.publish_presence.assert_awaited_once()
        mock_mqtt_manager.publish_log.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_presence_cooldown(self, attendance_system, mock_auth_manager, mock_mqtt_manager):
        """Teste le mécanisme de cooldown pour éviter les doublons"""
        # Première détection
        await attendance_system._on_presence_detected()
        
        # Vérifier le premier appel
        mock_auth_manager.authenticate_student.assert_awaited_once()
        mock_mqtt_manager.publish_presence.assert_awaited_once()
        
        # Réinitialiser les mocks
        mock_auth_manager.authenticate_student.reset_mock()
        mock_mqtt_manager.publish_presence.reset_mock()
        
        # Deuxième détection rapide (devrait être ignorée)
        await attendance_system._on_presence_detected()
        
        # Vérifier que le deuxième appel est traité mais la présence n'est pas publiée
        mock_auth_manager.authenticate_student.assert_awaited_once()
        mock_mqtt_manager.publish_presence.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, attendance_system, mock_mqtt_manager, mock_sensor, mock_camera, mock_rfid, mock_feedback):
        """Teste le nettoyage des ressources"""
        # Exécuter le nettoyage
        await attendance_system._cleanup()
        
        # Vérifier les appels aux méthodes
        mock_sensor.stop_monitoring.assert_awaited_once()
        mock_mqtt_manager.publish_status.assert_awaited_once()
        mock_mqtt_manager.disconnect.assert_awaited_once()
        mock_camera.cleanup.assert_called_once()
        if mock_rfid:
            mock_rfid.cleanup.assert_called_once()
        mock_feedback.play_pattern.assert_awaited()
        mock_feedback.cleanup.assert_called_once()

class TestAuthMQTTIntegration:
    """Tests d'intégration pour l'authentification et la communication MQTT"""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Crée un mock de DataManager"""
        data_manager = MagicMock(spec=DataManager)
        data_manager.find_matching_student = MagicMock(return_value=("12345", 0.95))
        return data_manager
    
    @pytest.fixture
    def mock_camera(self):
        """Crée un mock de CameraController"""
        camera = MagicMock(spec=CameraController)
        camera.capture_and_extract = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        return camera
    
    @pytest.fixture
    def mock_mqtt_manager(self):
        """Crée un mock de MQTTManager"""
        mqtt_manager = MagicMock(spec=MQTTManager)
        mqtt_manager.publish_presence = AsyncMock(return_value=True)
        return mqtt_manager
    
    @pytest.fixture
    def auth_manager(self, mock_data_manager, mock_camera):
        """Crée une instance d'AuthenticationManager avec des mocks"""
        return AuthenticationManager(mock_data_manager, mock_camera)
    
    @pytest.mark.asyncio
    async def test_auth_mqtt_pipeline(self, auth_manager, mock_data_manager, mock_mqtt_manager):
        """Teste le pipeline complet d'authentification et publication MQTT"""
        # 1. Authentifier un étudiant
        auth_result = await auth_manager.authenticate_student()
        
        # 2. Créer un message de présence
        presence_data = {
            "student_id": auth_result.student_id,
            "status": True,
            "module_uid": 1,
            "details": {
                "auth_method": auth_result.method,
                "confidence": auth_result.confidence
            }
        }
        
        # 3. Publier via MQTT
        await mock_mqtt_manager.publish_presence(presence_data)
        
        # Vérifier les résultats
        assert auth_result.success is True
        assert auth_result.student_id == "12345"
        mock_mqtt_manager.publish_presence.assert_awaited_once_with(presence_data)
