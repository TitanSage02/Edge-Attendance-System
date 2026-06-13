import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { toastManager } from "@/services/toastManager";
import axiosRetry from 'axios-retry';

/* ---------------------------------------------------------------------------
 * Instance Axios centralisée, compatible FastAPI refresh‑token (cookie)     
 * ------------------------------------------------------------------------- */
// Récupérer l'URL API depuis localStorage en priorité, sinon depuis les variables d'environnement
const savedApiUrl = localStorage.getItem('CREC_API_URL');
const baseURL = savedApiUrl || import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

interface ApiError {
  detail: string;
  code?: string;
  errors?: Record<string, string[]>;
}

interface RetryRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export const api: AxiosInstance = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // Pour envoyer le cookie refresh
  timeout: 15_000,
});

/* ---------------------------------------------------------------------------
 * Request : ajoute le JWT s'il existe (localStorage OU sessionStorage)
 * ------------------------------------------------------------------------- */
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// Configuration du retry
axiosRetry(api, { 
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) || error.response?.status === 429;
  }
});

// Amélioration de la gestion des erreurs
const handleApiError = (error: AxiosError<ApiError>) => {
  const status = error.response?.status;
  const data = error.response?.data as ApiError;
  
  // Si le backend a renvoyé un détail d'erreur, on l'utilise
  // if (data?.detail) {
  //   return data.detail;
  // }

  // Gestion spécifique des erreurs de validation
  if (data?.errors) {
    const [field, msgs] = Object.entries(data.errors)[0];
    return `${field}: ${msgs[0]}`;
  }

  // Messages d'erreur par défaut si pas de détail du backend
  const errorMessages: Record<number, string> = {
    400: "Requête invalide",
    401: "Adresse e-mail ou mot de passe incorrect.",
    403: "Accès refusé",
    404: "Ressource introuvable",
    422: "Données invalides",
    429: "Trop de requêtes, veuillez réessayer dans quelques instants",
    500: "Erreur interne du serveur",
    502: "Erreur de communication avec le serveur",
    503: "Service temporairement indisponible",
    504: "Délai d'attente dépassé"
  };

  return errorMessages[status || 0] || `Erreur ${status}`;
};

/* ---------------------------------------------------------------------------
 * Response : tente un /auth/refresh pour 401 expiré, sinon gère les erreurs
 * ------------------------------------------------------------------------- */
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiError>) => {
    const original = error.config as RetryRequestConfig;

    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    
    if (token && error.response?.status === 401 && !original?._retry) {
      original._retry = true;
      try {
        const { data } = await api.post(
          "/auth/refresh",
          null, 
          { headers: { "X-Refresh": "true" } }
        );
        const newToken: string = data.access_token;
        
        if (newToken) {
          // Mettre à jour le token dans le même storage que celui utilisé actuellement
          const currentStorage = localStorage.getItem("token") ? localStorage : sessionStorage;
          currentStorage.setItem("token", newToken);
          
          api.defaults.headers.common["Authorization"] = `Bearer ${newToken}`;
          original.headers!["Authorization"] = `Bearer ${newToken}`;
          
          return api(original);
        }
      } catch {
        // Gestion de l'échec du refresh
        localStorage.clear();
        sessionStorage.clear();
        toastManager.error("Session, expriée. Veuillez vous reconnecter");
        setTimeout(() => (window.location.href = "/login"), 1500);
        
        return Promise.reject(error);
      }
    }    
    const errorMessage = handleApiError(error);
    toastManager.error(errorMessage);
    return Promise.reject(error);
  }
);

/* ---------------------------------------------------------------------------
 * Re‑export des services générés manuellement
 * ------------------------------------------------------------------------- */
export * from "./api/auth";
export * from "./api/students";
export * from "./api/modules";
export * from "./api/presence";
export * from "./api/users";
export * from "./api/dashboard";
export * from "./api/settings";