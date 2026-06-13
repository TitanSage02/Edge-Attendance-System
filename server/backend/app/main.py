"""
Point d'entrée principal de l'application Edge Attendance System API.

Ce module configure l'application FastAPI, incluant la gestion du cycle de vie,
la journalisation des requêtes, la gestion des erreurs et la configuration CORS.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

import time
import logging

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.core.rate_limiter import RateLimiter

from app.api.v1.api import api_router

from sqlalchemy import select
from app.db.session import AsyncSessionLocal

from contextlib import asynccontextmanager
from app.services.log_service import db_logger

from app.utils.hashing import generate_password
from app.services.email_service import send_welcome_email 
from app.db.init_db import initialize_database


async def check_db():
    """
    Vérifie la connexion à la base de données et initialise les tables.
    Journalise le succès ou l'échec de la connexion.
    """
    try:
        # Initialisation automatique de la base de données
        if not await initialize_database():
            raise Exception("Échec de l'initialisation de la base de données")
            
        # Vérification finale de la connexion
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
            
            await db_logger.debug(
                "🟢 Base de données initialisée et connexion établie avec succès",
                source="système"
            )
            
    except Exception as e:
        await db_logger.error(
            "🔴 Echec de l'initialisation/connexion à la base de données",
            source="système",
            details={"erreur": str(e)}
        )
        raise

# Créer un premier utilisateur 
async def create_first_user():
    """
    Crée un premier utilisateur administrateur si aucun utilisateur n'existe.
    """
    try:
        from app.services.user_service import crud_user

        # Vérification de la base de données
        async with AsyncSessionLocal() as db:
            # Vérifie l'utilisateur avec l'email spécifié dans la configuration existe déjà
            first_user = await crud_user.get_by_email(db, email=str(settings.FIRST_USER_EMAIL))
            
            if not first_user:
                # Génération d'un mot de passe temporaire robuste
                raw_password = generate_password(length=8)

                # Crée le premier utilisateur admin avec le mot de passe hashé
                first_user = await crud_user.create(
                    db,
                    email=str(settings.FIRST_USER_EMAIL),
                    password=raw_password,
                    firstName=str(settings.FIRST_USER_FIRST_NAME),
                    lastName=str(settings.FIRST_USER_LAST_NAME), 
                    role="admin"
                )

                await db.commit()

                await db_logger.info(
                    "👨‍💼 Premier administrateur créé avec succès 🎉",
                    source="sécurité",
                    details={"email": str(settings.FIRST_USER_EMAIL), "action": "création_admin"}
                )

                # Envoi d'un email de bienvenue avec le mot de passe temporaire
                await send_welcome_email(
                    to=str(settings.FIRST_USER_EMAIL),
                    username=str(settings.FIRST_USER_FIRST_NAME),
                    password=raw_password
                )

            else:
                pass

    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la création du premier administrateur. Erreur : {str(e)}",
            source="create_admin"
        )
        raise



# Initialisation de la base de données et des services
@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """
    Gère le cycle de vie de l'application.
    Journalise le démarrage et l'arrêt de l'application.
    """
    # Vérification de la base de données et création du premier compte utilisateur si inexistant dans la bd
    await check_db()
    await create_first_user()
    
    # Initialisation du service MQTT
    from app.services.mqtt_service import initialize_mqtt, mqtt_client
    try:
        await initialize_mqtt()
    except Exception as e:
        await db_logger.error(f"❌ Erreur lors de l'initialisation MQTT: {str(e)}", source="système")
        # Ne pas arrêter l'application pour les erreurs MQTT
    
    # Initialisation du chatbot
    try:
        from app.services.chatbot.rag_system import chatbot
        await chatbot.initialize()
        chatbot.start_monitoring()
    except Exception as e:
        await db_logger.error(f"❌ Erreur lors de l'initialisation du chatbot: {str(e)}", source="système")
        # Ne pas arrêter l'application pour les erreurs de chatbot
    
    # Démarrage du vérificateur de statut des modules
    try:
        import asyncio
        from app.services.module_status_checker import run_status_checker
        
        # Démarrer la tâche de vérification périodique
        status_checker_task = asyncio.create_task(run_status_checker())
        await db_logger.debug(
            "🔄 Vérificateur de statut des modules démarré",
            source="système"
        )
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors du démarrage du vérificateur de statut des modules: {str(e)}",
            source="système"
        )
    
    await db_logger.info(
        "Le serveur Edge Attendance System a bien démarré avec succès",
        source="système"
    )

    yield
    
    # Arrêt propre du chatbot
    chatbot.stop_monitoring()
    
    # Arrêt du vérificateur de statut des modules
    if 'status_checker_task' in locals():
        status_checker_task.cancel()
        try:
            await status_checker_task
        except asyncio.CancelledError:
            pass
        await db_logger.debug(
            "🛑 Vérificateur de statut des modules arrêté",
            source="système"
        )
    
    # Déconnexion propre du service MQTT
    if mqtt_client and mqtt_client.connected:
        await mqtt_client.disconnect()
    
    await db_logger.debug(
        "🛑 Serveur Edge Attendance System arrêté proprement",
        source="système"
    )
    logging.shutdown() # Fermer les gestionnaires de logs proprement


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=_lifespan
)

origins = [
    "https://presence.crec-sj.org",        # front prod
    "https://www.presence.crec-sj.org",      
    "http://localhost:5000",              # front dev
]

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Liste des origines autorisées
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Ajouter le middleware de limitation de débit
app.add_middleware(
    RateLimiter,
    requests_per_minute=100,
    auth_requests_per_minute=10  # Plus restrictif pour les endpoints d'authentification
)

# Middleware pour la journalisation des requêtes et le suivi des performances
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware pour journaliser les requêtes entrantes et sortantes.
    Ajoute un en-tête de temps de traitement à la réponse.
    """
    start_time = time.time()
    
    # Créer un ID de requête pour suivre la requête à travers les composants
    request_id = request.headers.get("X-Request-ID", f"req-{time.time()}")
    request.state.request_id = request_id
 
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
    
        
        # Ajouter un en-tête de temps de traitement à la réponse
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur non gérée dans le middleware de journalisation: {str(e)}",
            source="middleware",
            details={
                "request_id": request_id,
                "erreur": str(e),
                "type_erreur": type(e).__name__,
                "endpoint": str(request.url.path),
                "methode": request.method
            }
        )
        
        # Retourner une réponse d'erreur générique
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne du serveur", "type": "erreur_interne"}
        )

# Gestionnaire d'exception global pour les erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Gestionnaire d'exception pour les erreurs de validation des requêtes.
    Journalise les erreurs et retourne une réponse JSON avec les détails de l'erreur.
    """
    await db_logger.warning(
        "⚠️ Données de requête invalides",
        source="validation",
        details={
            "endpoint": str(request.url.path),
            "methode": request.method,
            "erreurs_count": len(exc.errors())
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "type": "erreur_validation",
            "message": "Erreur de validation des données de la requête"
        }
    )

# Gestionnaire d'exception spécifique pour les erreurs SQLAlchemy
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Gestionnaire d'exception pour les erreurs SQLAlchemy.
    Journalise les erreurs et retourne une réponse JSON avec un message approprié.
    """
    # Gestion spécifique pour les erreurs "greenlet_spawn"
    if "greenlet_spawn has not been called" in str(exc):
        await db_logger.error(
            "🔧 Configuration de session asynchrone incorrecte ⚙️",
            source="base_données",
            details={
                "type_erreur": "MissingGreenlet",
                "endpoint": str(request.url.path),
                "solution": "Session async non initialisée"
            }
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Erreur de session de base de données asynchrone", 
                "type": "erreur_session_async"
            }
        )
    
    await db_logger.error(
        f"💾 Erreur de base de données détectée 🔧. Type d'erreur : {type(exc).__name__}, Endpoint : {str(request.url.path)}, Methode : {request.method}",
        source="base_données",
        details={
            "erreur_complete": str(exc),
            "cause_originale": str(exc.orig) if hasattr(exc, 'orig') else None,
            "code_erreur": getattr(exc, 'code', None)
        }
    )
    
    # Gestion spécifique selon le type d'erreur
    if isinstance(exc, IntegrityError):
        error_message = str(exc)
        # Gestion spécialisée pour les erreurs d'intégrité
        if "modules_uid_key" in error_message or "UNIQUE constraint failed: modules.uid" in error_message:
            return JSONResponse(
                status_code=409,  # Conflict
                content={
                    "detail": "Un module avec cet UID existe déjà", 
                    "type": "erreur_uid_existant"
                }
            )

        elif "duplicate key value violates unique constraint" in error_message or "UNIQUE constraint failed" in error_message:
            return JSONResponse(
                status_code=409,  # Conflict
                content={
                    "detail": "Violation de contrainte d'unicité", 
                    "type": "erreur_contrainte_unique"
                }
            )
        
        elif "foreign key constraint" in error_message.lower():
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Erreur de contrainte de clé étrangère", 
                    "type": "erreur_cle_etrangere"
                }
            )
        
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Erreur de contrainte de base de données", 
                    "type": "erreur_integrite_db"
                }
            )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erreur de base de données", 
            "type": "erreur_db"
        }
    )

# Gestionnaire d'exception global pour les exceptions HTTP
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Gestionnaire d'exception pour les exceptions HTTP.
    Journalise les erreurs et retourne une réponse JSON avec les détails de l'erreur.
    """
    # Journaliser seulement les erreurs importantes (500, 401, 403)
    if exc.status_code >= 500 or exc.status_code in [401, 403]:
        await db_logger.warning(
            f"🔐 Erreur HTTP {exc.status_code} détectée 🚨",
            source="sécurité" if exc.status_code in [401, 403] else "serveur",
            details={
                "code_statut": exc.status_code,
                "endpoint": str(request.url.path),
                "detail": exc.detail
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers or {},
        content={
            "detail": exc.detail,
            "type": "erreur_http",
            "code": exc.status_code
        }
    )

# Gestionnaire d'exception global pour les exceptions non gérées
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire d'exception global pour capturer toutes les exceptions non gérées.
    Journalise l'erreur et retourne une réponse JSON avec un message d'erreur générique.
    """
    # Gestion spéciale pour les erreurs de session de base de données
    if "PendingRollbackError" in str(type(exc)) or "rollback" in str(exc).lower():
        await db_logger.error(
            "💾 Transaction de base de données annulée ↩️",
            source="base_données",
            details={
                "type_erreur": type(exc).__name__,
                "endpoint": str(request.url.path),
                "action": "rollback_requis"
            }
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Erreur de base de données - transaction annulée", 
                "type": "erreur_session_db"
            }
        )
    
    await db_logger.error(
        f"💥 Erreur système inattendue détectée. Type d'erreur : {type(exc).__name__}; Endpoint : {str(request.url.path)}",
        source="système"
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur inattendue s'est produite", "type": "erreur_interne"}
    )

# Monter le routeur API
app.include_router(api_router, prefix="/api/v1")

# Endpoint de santé pour Docker health check
@app.get("/health")
async def health_check():
    """
    Endpoint de santé pour vérifier que l'API fonctionne correctement.
    Utilisé par Docker pour les health checks.
    """
    try:
        # Vérification rapide de la base de données
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        
        return {
            "status": "healthy",
            "service": "Edge Attendance System API",
            "version": settings.PROJECT_VERSION,
            "timestamp": time.time()
        }
    except Exception as e:
        # En cas d'erreur, retourner un statut 503
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Point de terminaison racine
@app.get("/")
async def root():
    """
    Point de terminaison racine retournant les informations de base de l'API.
    """
    await db_logger.info(
        "🏠 Page d'accueil API consultée",
        source="api"
    )

    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "documentation": "/api/docs"
    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
    )
    
    # Ajout de la documentation de sécurité
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema

    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.PROJECT_NAME} - Documentation API",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url
        # swagger_js_url="/static/swagger-ui-bundle.js",
        # swagger_css_url="/static/swagger-ui.css",
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)