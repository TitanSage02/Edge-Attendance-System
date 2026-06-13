/**
 * Utilitaires pour la gestion de l'authentification
 */

import { authApi } from "@/services/api/auth";

/**
 * Vérifie si l'utilisateur actuel a encore les bonnes permissions
 * en rafraîchissant son profil depuis le serveur
 */
export const validateCurrentUserPermissions = async (): Promise<boolean> => {
  try {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (!token) {
      return false;
    }

    // Récupérer le profil actuel depuis le serveur
    const currentUser = await authApi.getCurrentUser();
    
    // Vérifier que l'utilisateur existe toujours et est actif
    if (!currentUser || !currentUser.is_active) {
      // Nettoyer le stockage local si l'utilisateur n'est plus valide
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
      return false;
    }

    // Mettre à jour les données utilisateur dans le stockage
    const storage = localStorage.getItem("token") ? localStorage : sessionStorage;
    storage.setItem("user", JSON.stringify(currentUser));
    
    return true;
  } catch (error) {
    console.warn("Erreur lors de la validation des permissions:", error);
    
    // En cas d'erreur 401, nettoyer le stockage
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
    }
    
    return false;
  }
};

/**
 * Nettoie complètement l'authentification locale
 */
export const clearAuthData = (): void => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("user");
  
  // Nettoyer les headers axios
  import('@/services/api').then(({ api }) => {
    delete api.defaults.headers.common["Authorization"];
  });
};

/**
 * Vérifie si les données utilisateur en local sont cohérentes
 */
export const validateLocalUserData = (): boolean => {
  try {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const userRaw = localStorage.getItem("user") || sessionStorage.getItem("user");
    
    if (!token || !userRaw) {
      return false;
    }
    
    const user = JSON.parse(userRaw);
    
    // Vérifications de base
    if (!user || !user.email || !user.role || !user.id) {
      return false;
    }
    
    // Vérifier que l'utilisateur est actif
    if (user.is_active === false) {
      return false;
    }
    
    return true;
  } catch (error) {
    console.warn("Erreur lors de la validation des données utilisateur locales:", error);
    return false;
  }
};
