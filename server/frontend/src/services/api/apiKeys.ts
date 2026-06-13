import { api } from "../api";

// Types pour les clés API
export interface ApiKeyCreate {
  module_uid: number;
}

export interface ApiKeyRead {
  id: number;
  module_uid: number;
  created_at: string;
  last_used_at?: string;
  is_active: boolean;
  key: string;
}

export interface ApiKeyResponse {
  id: number;
  key: string;
  module_uid: number;
  created_at: string;
  last_used_at?: string;
  is_active: boolean;
  message: string;
}

/**
 * Service pour la gestion des clés API
 * Communication avec l'API backend /api/v1/api-keys
 */
export const apiKeysApi = {
  /**
   * Créer une nouvelle clé API pour un module
   */
  createApiKey: async (data: ApiKeyCreate): Promise<ApiKeyResponse> => {
    try {
      const response = await api.post("/api-keys/", data);
      return response.data;
    } catch (error: any) {
      console.error("Erreur lors de la création de la clé API:", error);
      throw new Error(
        error.response?.data?.detail || 
        "Erreur lors de la création de la clé API"
      );
    }
  },

  /**
   * Lister toutes les clés API
   */
  listApiKeys: async (
    includeInactive: boolean = false,
    moduleUid?: number
  ): Promise<ApiKeyRead[]> => {
    try {
      const params = new URLSearchParams();
      if (includeInactive) {
        params.append("include_inactive", "true");
      }
      if (moduleUid !== undefined) {
        params.append("module_uid", moduleUid.toString());
      }

      const response = await api.get(`/api-keys/?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      console.error("Erreur lors de la récupération des clés API:", error);
      throw new Error(
        error.response?.data?.detail || 
        "Erreur lors de la récupération des clés API"
      );
    }
  },

  /**
   * Récupérer une clé API spécifique
   */
  getApiKey: async (apiKeyId: number): Promise<ApiKeyRead> => {
    try {
      const response = await api.get(`/api-keys/${apiKeyId}`);
      return response.data;
    } catch (error: any) {
      console.error("Erreur lors de la récupération de la clé API:", error);
      throw new Error(
        error.response?.data?.detail || 
        "Erreur lors de la récupération de la clé API"
      );
    }
  },

  /**
   * Révoquer (désactiver) une clé API
   */
  revokeApiKey: async (apiKeyId: number): Promise<ApiKeyRead> => {
    try {
      const response = await api.patch(`/api-keys/${apiKeyId}/revoke`);
      return response.data;
    } catch (error: any) {
      console.error("Erreur lors de la révocation de la clé API:", error);
      throw new Error(
        error.response?.data?.detail || 
        "Erreur lors de la révocation de la clé API"
      );
    }
  },

  /**
   * Activer une clé API
   */
  activateApiKey: async (apiKeyId: number): Promise<ApiKeyRead> => {
    try {
      const response = await api.patch(`/api-keys/${apiKeyId}/activate`);
      return response.data;
    } catch (error: any) {
      console.error("Erreur lors de l'activation de la clé API:", error);
      throw new Error(
        error.response?.data?.detail || 
        "Erreur lors de l'activation de la clé API"
      );
    }
  },

  /**
   * Supprimer définitivement une clé API
   */
  deleteApiKey: async (apiKeyId: number): Promise<void> => {
    try {
      await api.delete(`/api-keys/${apiKeyId}`);
    } catch (error: any) {
      console.error("Erreur lors de la suppression de la clé API:", error);
      throw new Error(
        error.response?.data?.detail || 
        "Erreur lors de la suppression de la clé API"
      );
    }
  },
};
