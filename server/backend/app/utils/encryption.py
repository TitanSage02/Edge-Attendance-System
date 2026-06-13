"""
Module de chiffrement pour sécuriser les données sensibles.
Utilise AES-256 en mode GCM pour garantir confidentialité et authenticité des données.
"""
import os
import base64
from app.core.config import settings
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class EncryptionService:
    def __init__(self, key=None):
        """
        Initialise le service de chiffrement avec une clé.
        Si aucune clé n'est fournie, utilise la clé définie dans les paramètres de l'application.
        
        Args:
            key: Clé de chiffrement (32 octets pour AES-256) encodée en base64
        """
        if key is None:
            if not settings.ENCRYPTION_KEY:
                raise ValueError("Clé de chiffrement manquante dans les paramètres de l'application")
            
            key = base64.b64decode(settings.ENCRYPTION_KEY)
        
        elif isinstance(key, str):
            key = base64.b64decode(key)
        
        if len(key) != 32:
            raise ValueError("La clé de chiffrement doit faire 32 octets (256 bits) pour AES-256")
            
        self.key = key
        self.aesgcm = AESGCM(self.key)
        
    @staticmethod
    def generate_key():
        """
        Génère une nouvelle clé de chiffrement AES-256 encodée en base64.
        
        Returns:
            str: Clé encodée en base64
        """
        key = os.urandom(32)  # 32 octets = 256 bits
        return base64.b64encode(key).decode('utf-8')
    
    def encrypt(self, data):
        """
        Chiffre des données avec AES-256-GCM.
        
        Args:
            data: Données à chiffrer (chaîne, bytes, ou objet JSON sérialisable)
            
        Returns:
            str: Données chiffrées encodées en base64
        """
        if data is None:
            return None
            
        # Convertir en JSON si nécessaire puis en bytes
        if not isinstance(data, bytes):
            if not isinstance(data, str):
                import json
                data = json.dumps(data)
            data = data.encode('utf-8')
            
        # Générer un nonce aléatoire
        nonce = os.urandom(12)
        
        # Chiffrer les données
        encrypted = self.aesgcm.encrypt(nonce, data, None)
        
        # Concaténer nonce + données chiffrées et encoder en base64
        return base64.b64encode(nonce + encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data):
        """
        Déchiffre des données chiffrées avec AES-256-GCM.
        
        Args:
            encrypted_data: Données chiffrées encodées en base64
            
        Returns:
            bytes: Données déchiffrées
        """
        if encrypted_data is None:
            return None
            
        # Décoder de base64
        data = base64.b64decode(encrypted_data)
        
        # Extraire le nonce (12 premiers octets)
        nonce = data[:12]
        encrypted = data[12:]
        
        # Déchiffrer
        return self.aesgcm.decrypt(nonce, encrypted, None)
    
    # def decrypt_to_str(self, encrypted_data):
    #     """
    #     Déchiffre des données et les convertit en chaîne UTF-8.
        
    #     Args:
    #         encrypted_data: Données chiffrées encodées en base64
            
    #     Returns:
    #         str: Données déchiffrées sous forme de chaîne
    #     """
    #     if encrypted_data is None:
    #         return None
            
    #     decrypted = self.decrypt(encrypted_data)
    #     return decrypted.decode('utf-8')
    
    # def decrypt_to_json(self, encrypted_data):
    #     """
    #     Déchiffre des données et les parse comme du JSON.
        
    #     Args:
    #         encrypted_data: Données chiffrées encodées en base64
            
    #     Returns:
    #         dict/list: Données déchiffrées parsées depuis JSON
    #     """
    #     if encrypted_data is None:
    #         return None
            
    #     import json
    #     decrypted = self.decrypt_to_str(encrypted_data)
    #     return json.loads(decrypted)


# Instance singleton à utiliser dans l'application
encryption_service = EncryptionService()
