import { useCallback } from 'react';
import { toastManager, ToastConfig, ToastType } from '@/services/toastManager';

/**
 * Hook unifié pour la gestion des toasts
 * Remplace l'utilisation directe de useToast et toast de Sonner
 */
export const useUnifiedToast = () => {
  const showToast = useCallback((config: ToastConfig) => {
    return toastManager.show(config);
  }, []);

  const success = useCallback((description: string, options?: Partial<ToastConfig>) => {
    return toastManager.success(description, options);
  }, []);

  const error = useCallback((description: string, options?: Partial<ToastConfig>) => {
    return toastManager.error(description, options);
  }, []);

  const warning = useCallback((description: string, options?: Partial<ToastConfig>) => {
    return toastManager.warning(description, options);
  }, []);

  const info = useCallback((description: string, options?: Partial<ToastConfig>) => {
    return toastManager.info(description, options);
  }, []);

  const loading = useCallback((description: string, options?: Partial<ToastConfig>) => {
    return toastManager.loading(description, options);
  }, []);

  const dismiss = useCallback((id: string) => {
    toastManager.dismiss(id);
  }, []);

  const dismissAll = useCallback(() => {
    toastManager.dismissAll();
  }, []);

  const dismissByType = useCallback((type: ToastType) => {
    toastManager.dismissByType(type);
  }, []);

  const update = useCallback((id: string, config: Partial<ToastConfig>) => {
    toastManager.update(id, config);
  }, []);

  return {
    showToast,
    success,
    error,
    warning,
    info,
    loading,
    dismiss,
    dismissAll,
    dismissByType,
    update,
  };
};

export default useUnifiedToast;
