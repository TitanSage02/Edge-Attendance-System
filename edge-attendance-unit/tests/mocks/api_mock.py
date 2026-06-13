"""
Mock pour les appels API dans les tests
"""

import json
from unittest.mock import MagicMock
from aiohttp import ClientResponse, ClientSession
from typing import Dict, Any, List


class MockResponse(MagicMock):
    """Mock pour aiohttp.ClientResponse"""
    
    def __init__(self, status=200, content=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = status
        self._content = content or {}
    
    async def json(self):
        return self._content
    
    async def text(self):
        if isinstance(self._content, (dict, list)):
            return json.dumps(self._content)
        return str(self._content)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class MockClientSession:
    """Mock pour aiohttp.ClientSession"""
    
    def __init__(self, responses=None):
        """
        Args:
            responses: Dict[str, Dict] mapping URLs to response data
        """
        self.responses = responses or {}
        self.requests = []
    
    async def get(self, url, headers=None, **kwargs):
        """Mock pour la méthode GET"""
        self.requests.append({"method": "GET", "url": url, "headers": headers, "kwargs": kwargs})
        
        # Trouver la réponse correspondante
        for pattern, response in self.responses.items():
            if pattern in url:
                status = response.get("status", 200)
                content = response.get("content", {})
                return MockResponse(status=status, content=content)
        
        # Réponse par défaut
        return MockResponse(status=404, content={"error": "Not found"})
    
    async def post(self, url, headers=None, json=None, **kwargs):
        """Mock pour la méthode POST"""
        self.requests.append({
            "method": "POST", 
            "url": url, 
            "headers": headers, 
            "json": json,
            "kwargs": kwargs
        })
        
        # Trouver la réponse correspondante
        for pattern, response in self.responses.items():
            if pattern in url:
                status = response.get("status", 200)
                content = response.get("content", {})
                return MockResponse(status=status, content=content)
        
        # Réponse par défaut
        return MockResponse(status=404, content={"error": "Not found"})
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


def get_mock_students_data() -> List[Dict[str, Any]]:
    """Retourne des données fictives d'étudiants pour les tests"""
    return [
        {
            "studentId": "12345",
            "first_name": "John",
            "last_name": "Doe",
            "rfidUid": "ABCD1234",
            "faceEmbedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        },
        {
            "studentId": "67890",
            "first_name": "Jane",
            "last_name": "Smith",
            "rfidUid": "EFGH5678",
            "faceEmbedding": [0.5, 0.4, 0.3, 0.2, 0.1]
        }
    ]
