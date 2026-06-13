import { useState, useEffect, useCallback } from "react";
import { 
  apiKeysApi, 
  ApiKeyCreate, 
  ApiKeyRead, 
  ApiKeyResponse 
} from "@/services/api/apiKeys";

export const useApiKeys = () => {
  const [apiKeys, setApiKeys] = useState<ApiKeyRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastCreatedKey, setLastCreatedKey] = useState<ApiKeyResponse | null>(null);

  // Charger les clés API
  const loadApiKeys = useCallback(async (includeInactive: boolean = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const keys = await apiKeysApi.listApiKeys(includeInactive);
      setApiKeys(keys);
    } catch (err: any) {
      setError(err.message);
      console.error("Erreur lors du chargement des clés API:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Créer une nouvelle clé API
  const createApiKey = useCallback(async (data: ApiKeyCreate): Promise<ApiKeyResponse | null> => {
    setCreating(true);
    setError(null);
    
    try {
      const newKey = await apiKeysApi.createApiKey(data);
      setLastCreatedKey(newKey);
      
      // Recharger la liste après création
      await loadApiKeys();
      
      return newKey;
    } catch (err: any) {
      setError(err.message);
      console.error("Erreur lors de la création de la clé API:", err);
      return null;
    } finally {
      setCreating(false);
    }
  }, [loadApiKeys]);

  // Révoquer une clé API
  const revokeApiKey = useCallback(async (apiKeyId: number): Promise<boolean> => {
    setError(null);
    
    try {
      await apiKeysApi.revokeApiKey(apiKeyId);
      
      // Mettre à jour la liste localement
      setApiKeys(prevKeys => 
        prevKeys.map(key => 
          key.id === apiKeyId 
            ? { ...key, is_active: false }
            : key
        )
      );
      
      return true;
    } catch (err: any) {
      setError(err.message);
      console.error("Erreur lors de la révocation de la clé API:", err);
      return false;
    }
  }, []);

  // Activer une clé API
  const activateApiKey = useCallback(async (apiKeyId: number): Promise<boolean> => {
    setError(null);
    
    try {
      await apiKeysApi.activateApiKey(apiKeyId);
      
      // Mettre à jour la liste localement
      setApiKeys(prevKeys => 
        prevKeys.map(key => 
          key.id === apiKeyId 
            ? { ...key, is_active: true }
            : key
        )
      );
      
      return true;
    } catch (err: any) {
      setError(err.message);
      console.error("Erreur lors de l'activation de la clé API:", err);
      return false;
    }
  }, []);

  // Supprimer une clé API
  const deleteApiKey = useCallback(async (apiKeyId: number): Promise<boolean> => {
    setError(null);
    
    try {
      await apiKeysApi.deleteApiKey(apiKeyId);
      
      // Retirer la clé de la liste localement
      setApiKeys(prevKeys => 
        prevKeys.filter(key => key.id !== apiKeyId)
      );
      
      return true;
    } catch (err: any) {
      setError(err.message);
      console.error("Erreur lors de la suppression de la clé API:", err);
      return false;
    }
  }, []);

  // Effacer la dernière clé créée (après l'avoir copiée)
  const clearLastCreatedKey = useCallback(() => {
    setLastCreatedKey(null);
  }, []);

  // Effacer les erreurs
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Charger automatiquement au montage du composant
  useEffect(() => {
    loadApiKeys();
  }, [loadApiKeys]);

  return {
    apiKeys,
    loading,
    creating,
    error,
    lastCreatedKey,
    loadApiKeys,
    createApiKey,
    revokeApiKey,
    activateApiKey,
    deleteApiKey,
    clearLastCreatedKey,
    clearError,
  };
};
