import axios from "axios";
import { configService } from "../config";

// Créer une instance axios avec la configuration de base
export const api = axios.create({
  baseURL: configService.apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
  // Timeout augmenté pour accommoder le backend local (utilise la config)
  timeout: configService.apiTimeout, 
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
    // Timeouts spécifiques selon le type de requête
  if (config.url?.includes('/export') || config.url?.includes('/backup')) {
    // Timeout plus long pour les exports et sauvegardes
    config.timeout = configService.longTimeout; // 5 minutes par défaut
  } else if (config.url?.includes('/embeddings') || config.url?.includes('/chat') || config.url?.includes('/ai')) {
    // Timeout plus long pour les IA et embeddings
    config.timeout = configService.heavyTimeout; // 10 minutes par défaut
  }
  
  // Log des requêtes en mode debug
  if (configService.isDebugMode) {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url} (timeout: ${config.timeout}ms)`);
  }
  
  return config;
});

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => {
    // Log des réponses en mode debug
    if (configService.isDebugMode) {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    // Log des erreurs en mode debug
    if (configService.isDebugMode) {
      const isTimeout = error.code === 'ECONNABORTED';
      console.error(`❌ API Error: ${error.response?.status || (isTimeout ? 'TIMEOUT' : 'NETWORK')} ${error.config?.url}`, error);
      
      if (isTimeout) {
        console.warn(`⏰ Requête expirée après ${error.config?.timeout}ms. Considérez augmenter le timeout pour cette opération.`);
      }
    }
    
    if (error.response?.status === 401) {
      // Nettoyer complètement le stockage local
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
      
      // Supprimer l'header d'autorisation
      delete api.defaults.headers.common["Authorization"];
      
      // Rediriger vers la page de connexion si le token est invalide
      window.location.href = "/login";
    } else if (error.response?.status === 403) {
      // Pour les erreurs 403, rediriger vers dashboard avec un message
      if (window.location.pathname !== '/dashboard') {
        window.location.href = "/dashboard";
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Crée une instance API avec un timeout personnalisé pour des opérations longues
 */
export const createApiWithTimeout = (timeoutMs: number) => {
  const apiInstance = axios.create({
    baseURL: configService.apiUrl,
    headers: {
      "Content-Type": "application/json",
    },
    timeout: timeoutMs,
  });

  // Appliquer les mêmes intercepteurs
  apiInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    if (configService.isDebugMode) {
      console.log(`🌐 API Request (custom timeout): ${config.method?.toUpperCase()} ${config.url} (timeout: ${timeoutMs}ms)`);
    }
    
    return config;
  });

  apiInstance.interceptors.response.use(
    (response) => {
      if (configService.isDebugMode) {
        console.log(`✅ API Response (custom timeout): ${response.status} ${response.config.url}`);
      }
      return response;
    },
    (error) => {
      if (configService.isDebugMode) {
        const isTimeout = error.code === 'ECONNABORTED';
        console.error(`❌ API Error (custom timeout): ${error.response?.status || (isTimeout ? 'TIMEOUT' : 'NETWORK')} ${error.config?.url}`, error);
      }
      
      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );

  return apiInstance;
};

/**
 * Instance API pour les opérations longues (exports, sauvegardes, etc.)
 */
export const longOperationApi = createApiWithTimeout(configService.longTimeout);

/**
 * Instance API pour les opérations très longues (IA, traitement lourd)
 */
export const heavyOperationApi = createApiWithTimeout(configService.heavyTimeout);

/**
 * Ajuste dynamiquement les timeouts selon les conditions réseau
 * Détecte si on est sur un backend local et adapte les timeouts
 */
export const getAdaptiveTimeout = (operationType: 'normal' | 'long' | 'heavy' = 'normal'): number => {
  const baseUrl = configService.apiUrl;
  const isLocalBackend = baseUrl.includes('localhost') || baseUrl.includes('127.0.0.1') || baseUrl.includes('ngrok');
  
  // Multiplicateur pour backend local (plus lent)
  const localMultiplier = isLocalBackend ? 1.5 : 1;
  
  switch (operationType) {
    case 'long':
      return Math.round(configService.longTimeout * localMultiplier);
    case 'heavy':
      return Math.round(configService.heavyTimeout * localMultiplier);
    default:
      return Math.round(configService.apiTimeout * localMultiplier);
  }
};

/**
 * Crée une instance API avec timeout adaptatif selon les conditions réseau
 */
export const createAdaptiveApi = (operationType: 'normal' | 'long' | 'heavy' = 'normal') => {
  const timeout = getAdaptiveTimeout(operationType);
  
  if (configService.isDebugMode) {
    console.log(`🌐 Création instance API adaptative: ${operationType} (timeout: ${timeout}ms)`);
  }
  
  return createApiWithTimeout(timeout);
};