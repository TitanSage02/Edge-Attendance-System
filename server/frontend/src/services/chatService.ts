/**
 * Service API pour les interactions avec le chatbot RAG.
 * Gère les appels vers l'API backend pour les fonctionnalités de chat.
 */

import { api } from "./api";

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  message: string;
}

export interface ChatHealthCheck {
  status: "healthy" | "unhealthy";
  details: Record<string, any>;
}

class ChatService {
  /**
   * Envoie un message au chatbot et retourne la réponse.
   */ 
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await api.post<ChatResponse>("chat/", {
        question: message.trim()
      });
      
      return response.data;
    } catch (error: any) {
      // Gestion des erreurs API
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.response?.status === 500) {
        throw new Error("Le service de chat rencontre des difficultés. Veuillez réessayer.");
      } else if (error.response?.status === 400) {
        throw new Error("Votre message n'est pas valide. Veuillez vérifier et réessayer.");
      } else if (!navigator.onLine) {
        throw new Error("Connexion internet requise pour utiliser le chat.");
      } else {
        throw new Error("Erreur de communication avec le serveur.");
      }
    }
  }

  /**
   * Vérifie l'état de santé du service de chat.
   */ 
  async getHealthStatus(): Promise<ChatHealthCheck> {
    try {
      const response = await api.get<ChatHealthCheck>("chat/health");
      return response.data;
    } catch (error: any) {
      console.error("Erreur lors de la vérification de santé du chat:", error);
      return {
        status: "unhealthy",
        details: { error: "Impossible de se connecter au service de chat" },
      };
    }
  }
}

// Instance singleton du service
export const chatService = new ChatService();

// Export par défaut
export default chatService;
