import { useCallback, useEffect, useRef } from 'react';
import { useAuth } from './useAuth';
import { validateCurrentUserPermissions } from '@/utils/authUtils';

/**
 * Hook pour gérer la validation périodique des permissions utilisateur
 * Particulièrement utile pour les pages administratives sensibles
 */
export const usePermissionValidator = (
  requiredRoles?: string[], 
  validationIntervalMs: number = 60 * 60 * 1000 // 1 heure par défaut
) => {
  const { isAuthenticated, logout, user } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout>();
  const lastValidationRef = useRef<number>(0);

  const validatePermissions = useCallback(async (): Promise<boolean> => {
    if (!isAuthenticated || !requiredRoles || requiredRoles.length === 0) {
      return true;
    }

    try {
      const now = Date.now();
      // Éviter les validations trop fréquentes
      if (now - lastValidationRef.current < 30000) { // 30 secondes minimum
        return true;
      }

      lastValidationRef.current = now;
      const isValid = await validateCurrentUserPermissions();
      
      if (!isValid) {
        console.warn('Permissions révoquées détectées lors de la validation périodique');
        await logout();
        return false;
      }

      return true;
    } catch (error) {
      console.warn('Erreur lors de la validation périodique des permissions:', error);
      // En cas d'erreur réseau temporaire, on ne déconnecte pas immédiatement
      return true;
    }
  }, [isAuthenticated, requiredRoles, logout]);

  // Démarrer la validation périodique pour les pages sensibles
  useEffect(() => {
    if (!isAuthenticated || !requiredRoles || requiredRoles.length === 0) {
      return;
    }

    // Validation immédiate
    validatePermissions();

    // Validation périodique
    intervalRef.current = setInterval(validatePermissions, validationIntervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAuthenticated, requiredRoles, validationIntervalMs, validatePermissions]);

  // Nettoyage à la déconnexion
  useEffect(() => {
    if (!isAuthenticated && intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  }, [isAuthenticated]);

  return {
    validatePermissions,
    user,
    isAuthenticated
  };
};
