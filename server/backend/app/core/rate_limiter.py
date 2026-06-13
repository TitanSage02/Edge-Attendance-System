"""
Middleware pour limiter le taux de requêtes dans l'API.
Protège contre les attaques par force brute et le scraping abusif.
"""

import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.log_service import db_logger

class RateLimiter(BaseHTTPMiddleware):
    def __init__(
        self, 
        app, 
        requests_per_minute=60,
        auth_requests_per_minute=5,
        window_size=60
    ):
        """
        Initialise le middleware de limitation de débit.
        
        Args:
            app: Application FastAPI
            requests_per_minute: Nombre de requêtes autorisées par minute par IP
            auth_requests_per_minute: Nombre de requêtes d'authentification autorisées par minute par IP
            window_size: Taille de la fenêtre en secondes
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        self.window_size = window_size
        
        # Dictionnaire IP -> liste d'horodatages des requêtes
        self.request_records = defaultdict(list)
        
        # Dictionnaire IP -> liste d'horodatages des requêtes d'authentification
        self.auth_request_records = defaultdict(list)
        
        # Liste des chemins d'authentification à limite spéciale
        self.auth_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/reset-password"
        ]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        path = request.url.path
        
        # Choisir le dictionnaire approprié selon le chemin
        if path in self.auth_paths:
            records = self.auth_request_records[client_ip]
            limit = self.auth_requests_per_minute
        else:
            records = self.request_records[client_ip]
            limit = self.requests_per_minute
        
        # Nettoyer les enregistrements expirés
        records = [timestamp for timestamp in records 
                    if now - timestamp < self.window_size]
        
        # Mettre à jour les enregistrements
        if path in self.auth_paths:
            self.auth_request_records[client_ip] = records
        else:
            self.request_records[client_ip] = records
        
        # Vérifier la limite
        if len(records) >= limit:
            await db_logger.warning(
                f"Limite de débit dépassée pour {client_ip}",
                source="rate_limiter",
                details={
                    "ip": client_ip,
                    "path": path,
                    "requests_count": len(records),
                    "limit": limit
                }
            )
            
            # Retourner une réponse 429 Too Many Requests
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trop de requêtes. Veuillez réessayer plus tard."
            )
            
        # Ajouter l'horodatage actuel
        if path in self.auth_paths:
            self.auth_request_records[client_ip].append(now)
        else:
            self.request_records[client_ip].append(now)
        
        # Continuer le traitement normal
        response = await call_next(request)
        return response