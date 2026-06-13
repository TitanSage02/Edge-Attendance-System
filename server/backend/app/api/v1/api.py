"""API v1 router configuration.

This module sets up the main API router and includes all sub-routers for different
endpoints like authentication and chatbot functionality.
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.students import router as students_router
from app.api.v1.classes import router as classes_router
from app.api.v1.modules import router as modules_router
from app.api.v1.presence import router as presence_router
from app.api.v1.embeddings import router as embeddings_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.settings import router as settings_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.ws import router as ws_router
from app.api.v1.chat import router as chat_router


api_router = APIRouter()

# Include routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(students_router, prefix="/students", tags=["students"])
api_router.include_router(classes_router, prefix="/classes", tags=["classes"])
api_router.include_router(modules_router, prefix="/modules", tags=["modules"])
api_router.include_router(presence_router, prefix="/presences", tags=["presences"])
api_router.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(api_keys_router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(ws_router, prefix="/ws", tags=["websockets"])
api_router.include_router(chat_router, prefix="/chat", tags=["chatbot"])

@api_router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status information.
    """
    return {"status": "healthy", "version": "1.0.0", "author" : "Espérance AYIWAHOUN"}