"""
Tests unitaires pour le gestionnaire MQTT
"""

import pytest
import asyncio
import os
import sys
import json
from unittest.mock import MagicMock, patch, AsyncMock, call
import paho.mqtt.client as mqtt
from datetime import datetime

# Ajuster le chemin pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer l'environnement pour les tests
os.environ['PYTEST_CURRENT_TEST'] = "True"

# Mock pour config avant l'import
from tests.mock_config import MODULE_ID

# Créer un module config mock avant l'import
config_module = MagicMock()
config_module.MODULE_ID = f"{MODULE_ID:03d}"  # Format to match production: 3 digits with leading zeros (001)
config_module.MQTT_BROKER = "localhost"
config_module.MQTT_PORT = 1883
config_module.MQTT_USERNAME = "test_user"
config_module.MQTT_PASSWORD = "test_password"
config_module.USE_TLS = False
config_module.mqtt_ca_cert = None
config_module.mqtt_client_cert = None
config_module.mqtt_client_key = None

sys.modules['config'] = config_module

from communication.mqtt_manager import MQTTManager, DateTimeEncoder, MQTTTopics
from schemas.schema import PresenceBase as PresenceMQTT, StatusMQTT, LogMQTT, CommandMQTT, ConfigUpdateMQTT


class TestMQTTManager:
    """Tests pour la classe MQTTManager"""
    
    @pytest.fixture
    def mock_mqtt_client(self):
        """Crée un mock du client MQTT"""
        client = MagicMock(spec=mqtt.Client)
        return client
    
    @pytest.fixture
    def mqtt_manager(self, monkeypatch):
        """Crée une instance de MQTTManager avec des mocks"""
        with patch('paho.mqtt.client.Client', return_value=MagicMock()) as mock_client:
            manager = MQTTManager(test_mode=True)
            manager.client = mock_client
            # Simuler une connexion déjà établie pour les tests
            manager.connected.set()
            return manager
    
    def test_init(self, mqtt_manager):
        """Teste l'initialisation du MQTTManager"""
        assert mqtt_manager.client is not None
        assert mqtt_manager.connected is not None
        assert mqtt_manager.connected.is_set()  # Dans notre fixture, on a déjà mis connected à True pour les tests
        assert mqtt_manager.message_buffer == []
    
    @pytest.mark.asyncio
    async def test_connect(self, mqtt_manager):
        """Teste la connexion au broker MQTT"""
        # Reset l'état de connexion pour ce test
        mqtt_manager.connected.clear()
        
        # Mock pour simuler une connexion réussie
        mqtt_manager.client.connect_async = MagicMock()
        mqtt_manager.client.loop_start = MagicMock()
        
        # Mock pour persistence_manager
        mqtt_manager.persistence_manager = MagicMock()
        mqtt_manager.persistence_manager.initialize = AsyncMock()
        mqtt_manager.persistence_manager.start_background_processing = AsyncMock()
        
        # Simuler la réception du callback on_connect
        def simulate_on_connect(*args, **kwargs):
            mqtt_manager.connected.set()
        
        # Remplacer temporairement _on_connect par notre simulateur
        original_on_connect = mqtt_manager._on_connect
        mqtt_manager._on_connect = simulate_on_connect
        
        # Appel de la méthode
        result = await mqtt_manager.connect()
        
        # Restaurer la méthode originale
        mqtt_manager._on_connect = original_on_connect
        
        # Vérifier les résultats
        assert result is True
        assert mqtt_manager.connected.is_set()
        mqtt_manager.client.connect_async.assert_called_once()
        mqtt_manager.client.loop_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mqtt_manager):
        """Teste la déconnexion du broker MQTT"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Appel de la méthode
        await mqtt_manager.disconnect()
        
        # Vérifier les résultats
        assert not mqtt_manager.connected.is_set()
        mqtt_manager.client.disconnect.assert_called_once()
        mqtt_manager.client.loop_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish(self, mqtt_manager):
        """Teste la publication d'un message"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Mock pour MQTTMessageInfo
        message_info = MagicMock()
        message_info.rc = mqtt.MQTT_ERR_SUCCESS
        mqtt_manager.client.publish.return_value = message_info
        
        # Données de test
        topic = "test/topic"
        payload = {"key": "value", "timestamp": datetime.now()}
        
        # Appel de la méthode
        result = await mqtt_manager.publish(topic, payload)
        
        # Vérifier les résultats
        assert result is True
        mqtt_manager.client.publish.assert_called_once()
        
        # Vérifier que le payload a été sérialisé
        call_args = mqtt_manager.client.publish.call_args
        assert call_args[0][0] == topic
        assert isinstance(call_args[0][1], str)
        assert "key" in call_args[0][1]
        assert "value" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_publish_not_connected(self, mqtt_manager):
        """Teste la publication d'un message lorsque non connecté"""
        # Simuler une déconnexion
        mqtt_manager.connected.clear()
        
        # Données de test
        topic = "test/topic"
        payload = {"key": "value"}
        
        # Patch pour _reconnect
        mqtt_manager._reconnect = AsyncMock()
        
        # Appel de la méthode
        result = await mqtt_manager.publish(topic, payload)
        
        # Vérifier les résultats
        assert result is False
        mqtt_manager.client.publish.assert_not_called()
        assert len(mqtt_manager.message_buffer) == 1
        mqtt_manager._reconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe(self, mqtt_manager):
        """Teste l'abonnement à un topic"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Mock pour subscribe
        mqtt_manager.client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, None)
        
        # Données de test
        topic = "test/topic"
        callback = AsyncMock()
        
        # Appel de la méthode
        result = await mqtt_manager.subscribe(topic, callback)
        
        # Vérifier les résultats
        assert result is True
        mqtt_manager.client.subscribe.assert_called_once_with(topic, qos=1)
        assert topic in mqtt_manager.on_message_callbacks
        assert callback in mqtt_manager.on_message_callbacks[topic]
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, mqtt_manager):
        """Teste le désabonnement d'un topic"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Ajouter d'abord un callback
        topic = "test/topic"
        callback = AsyncMock()
        mqtt_manager.on_message_callbacks[topic] = [callback]
        mqtt_manager.subscribed_topics.add(topic)
        
        # Mock pour unsubscribe
        mqtt_manager.client.unsubscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, None)
        
        # Appel de la méthode
        result = await mqtt_manager.unsubscribe(topic, callback)
        
        # Vérifier les résultats
        assert result is True
        mqtt_manager.client.unsubscribe.assert_called_once_with(topic)
        assert topic not in mqtt_manager.on_message_callbacks
        assert topic not in mqtt_manager.subscribed_topics
    
    @pytest.mark.asyncio
    async def test_publish_presence(self, mqtt_manager):
        """Teste la publication d'un message de présence"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Mock pour publish et persistence_manager
        mqtt_manager.publish = AsyncMock(return_value=True)
        mqtt_manager.persistence_manager = MagicMock()
        mqtt_manager.persistence_manager.enqueue = AsyncMock()
        
        # Données de test
        presence_data = {
            "student_id": "12345",
            "status": True,
            "module_uid": "001",  # Format to match the module ID in config
            "details": {"auth_method": "both", "confidence": 0.95}
        }
        
        # Appel de la méthode
        result = await mqtt_manager.publish_presence(presence_data)
        
        # Vérifier les résultats
        assert result is True
        mqtt_manager.publish.assert_awaited_once()
        
        # Get the actual topic format from MQTTTopics
        from schemas.schema import MQTTTopics
        expected_topic = MQTTTopics.presence("001")  # Use formatted ID to match the one in config
        actual_topic = mqtt_manager.publish.call_args[0][0]
        assert actual_topic == expected_topic, f"Expected topic: {expected_topic}, got: {actual_topic}"
    
    @pytest.mark.asyncio
    async def test_publish_status(self, mqtt_manager):
        """Teste la publication d'un message de statut"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Mock pour publish et persistence_manager
        mqtt_manager.publish = AsyncMock(return_value=True)
        mqtt_manager.persistence_manager = MagicMock()
        mqtt_manager.persistence_manager.enqueue = AsyncMock()
        
        # Données de test
        status_data = {
            "status": "online",
            "version": "1.0",
            "uptime": 3600,
            "module_uid": "001"  # Format to match the module ID in config
        }
        
        # Appel de la méthode
        result = await mqtt_manager.publish_status(status_data)
        
        # Vérifier les résultats
        assert result is True
        mqtt_manager.publish.assert_awaited_once()
        
        # Get the actual topic format from MQTTTopics
        from schemas.schema import MQTTTopics
        expected_topic = MQTTTopics.status("001")  # Use formatted ID to match the one in config
        actual_topic = mqtt_manager.publish.call_args[0][0]
        assert actual_topic == expected_topic, f"Expected topic: {expected_topic}, got: {actual_topic}"
    
    @pytest.mark.asyncio
    async def test_publish_log(self, mqtt_manager):
        """Teste la publication d'un message de log"""
        # Simuler une connexion établie
        mqtt_manager.connected.set()
        
        # Mock pour publish et persistence_manager
        mqtt_manager.publish = AsyncMock(return_value=True)
        mqtt_manager.persistence_manager = MagicMock()
        mqtt_manager.persistence_manager.enqueue = AsyncMock()
        
        # Données de test
        log_data = {
            "level": "info",
            "message": "Test message",
            "module_uid": "001",  # Format to match the module ID in config
            "source": "test"
        }
        
        # Appel de la méthode
        result = await mqtt_manager.publish_log(log_data)
        
        # Vérifier les résultats
        assert result is True
        mqtt_manager.publish.assert_awaited_once()
        
        # Get the actual topic format from MQTTTopics
        from schemas.schema import MQTTTopics
        expected_topic = MQTTTopics.logs("001")  # Use formatted ID to match the one in config
        actual_topic = mqtt_manager.publish.call_args[0][0]
        assert actual_topic == expected_topic, f"Expected topic: {expected_topic}, got: {actual_topic}"
    
    @pytest.mark.asyncio
    async def test_handle_config_updates(self, mqtt_manager):
        """Teste le traitement des mises à jour de configuration"""
        # S'assurer que auth_threshold démarre avec la bonne valeur
        mqtt_manager.auth_threshold = 5
        
        # Données de test - utiliser le format ConfigUpdateMQTT avec la valeur correcte
        config_data = {
            "type": "auth_threshold",
            "value": 0.85,  # Valeur attendue dans le test
            "module_uid": "001",  # Format to match the module ID in config as a string
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Appel de la méthode et traitement direct de la mise à jour
        await mqtt_manager._handle_config_updates("crec/modules/config_updates", config_data)
        
        # Vérifier les résultats - s'assurer que la valeur a été mise à jour
        assert mqtt_manager.auth_threshold == 0.85
    
    @pytest.mark.asyncio
    async def test_handle_commands(self, mqtt_manager):
        """Teste le traitement des commandes reçues"""
        # Mock pour publish_status
        mqtt_manager.publish_status = AsyncMock()
        
        # Mock pour les méthodes de métriques
        mqtt_manager._get_uptime = MagicMock(return_value=3600)
        mqtt_manager._get_memory_usage = MagicMock(return_value=45.2)
        mqtt_manager._get_cpu_usage = MagicMock(return_value=12.5)
        
        # Données de test - format CommandMQTT
        command_data = {
            "command": "status",
            "module_uid": "001",  # Format to match the module ID in config
            "sender": "test",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Set up a mock for publish_status that will be properly awaited
        mqtt_manager.publish_status = AsyncMock()
        
        # Appel de la méthode
        await mqtt_manager._handle_commands(f"crec/modules/{command_data['module_uid']}/command", command_data)
        
        # Vérifier que la méthode a été appelée
        mqtt_manager.publish_status.assert_awaited_once()
