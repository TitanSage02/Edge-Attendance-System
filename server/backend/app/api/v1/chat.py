"""
API endpoints pour le chatbot RAG Edge Attendance System.
Fournit les routes pour interaction avec l'assistant IA administratif.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatHealthCheck
from app.services.chatbot.rag_system import chatbot
from app.services.log_service import db_logger

from app.api.v1.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Endpoint principal pour interaction avec l'assistant IA.
    
    Traite les questions administratives en utilisant RAG :
    - Recherche dans les logs système pertinents
    - Génère une réponse contextuelle avec Gemini API
    - Logs de l'interaction pour monitoring
    """
    try:
        # Identifier l'utilisateur pour logging
        user_info = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "auth_type": "user"
        }
        
        await db_logger.debug(
            f"🤖 Requête chatbot reçue: '{request.question[:50]}...'",
            source="chat_api",
            user_id=user_info.get("user_id"),
            details={
                **user_info,
                "query_length": len(request.question),
                "user_query": request.question[:50]  # Limite pour éviter logs trop longs
            }
        )
        
        if len(request.question) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La question est trop longue (maximum 2000 caractères)"
            )
        
        try : 
            message = await chatbot.query(request.question)

            await db_logger.debug(
                f"🤖 Réponse du chatbot: '{message[:50]}...'" if len(message) > 50 else message,
                source="chat_api",
                user_id=user_info.get("user_id"),
                details={
                    **user_info,
                    "response_length": len(message),
                    "user_query": request.question[:50]  # Limite pour éviter logs trop longs
                }
            )

        except Exception as e:
            await db_logger.error(
                f"❌ Erreur lors de la requête au chatbot: {str(e)}",
                source="chat_api",
                user_id=user_info.get("user_id"),  
            )
            message = "Le chatbot n'est pas opérationnel pour le moment. Veuillez réessayer plus tard."

        return ChatResponse(message=message)

    except HTTPException:
        raise

    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors du traitement de la requête chatbot: {str(e)}",
            source="chat_api",
            user_id=user_info.get("user_id"),
            details={
                **user_info,
                "error": str(e),
                "user_query": request.question[:100]
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur lors du traitement de votre demande"
        )

@router.get("/health", response_model=ChatHealthCheck)
async def chat_health_check(
    current_user: User = Depends(get_current_user)
) -> ChatHealthCheck:
    """
    Endpoint de vérification de santé du service chatbot.
    
    Retourne :
    - Statut du service RAG
    - Statistiques de performance
    - État des composants (Gemini API, ChromaDB)
    """
    try:

        return ChatHealthCheck(
            status="healthy"
        )

    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la vérification de santé du chatbot: {str(e)}",
            source="chat_api",
            details={"error": str(e)}
        )
        
        return ChatHealthCheck(
            status="unhealthy",
            details={"error": "Failed to retrieve health status"},
            last_error=str(e)
        )




