from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Modèle pour les requêtes du chatbot."""
    question: str = Field(..., min_length=1, max_length=1000, description="Question à poser au chatbot")

class ChatResponse(BaseModel):
    """Modèle pour les réponses du chatbot."""
    message: str = Field(..., description="Réponse générée par le chatbot")

class ChatError(BaseModel):
    """Modèle pour les erreurs du chatbot."""
    error: str = Field(..., description="Message d'erreur")
    error_code: str = Field(..., description="Code d'erreur")
    
class ChatHealthCheck(BaseModel):
    """Modèle pour le statut de santé du chatbot."""
    status: str = Field(..., description="Statut du service (healthy/unhealthy)")