import { toast as sonnerToast } from "sonner";
import { toast as radixToast } from "@/hooks/use-toast";

/**
 * Types de toasts disponibles
 */
export type ToastType = "success" | "error" | "warning" | "info" | "loading";

/**
 * Configuration d'un toast
 */
export interface ToastConfig {
  id?: string;
  title?: string;
  description: string;
  type?: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible?: boolean;
}

/**
 * Configuration par défaut pour chaque type de toast
 */
const DEFAULT_DURATIONS: Record<ToastType, number> = {
  success: 4000,
  error: 8000,
  warning: 6000,
  info: 4000,
  loading: 0, // Infini par défaut
};

/**
 * Gestionnaire unifié des toasts pour éviter les doublons et harmoniser l'affichage
 */
class ToastManager {
  private activeToasts = new Map<string, { timeoutId?: NodeJS.Timeout; dismiss?: () => void }>();
  private messageHashes = new Set<string>();
  
  /**
   * Génère un hash pour un message afin d'éviter les doublons
   */
  private generateMessageHash(config: ToastConfig): string {
    const content = `${config.type || 'info'}-${config.title || ''}-${config.description}`;
    return btoa(content).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
  }

  /**
   * Vérifie si un message similaire est déjà affiché
   */
  private isDuplicate(config: ToastConfig): boolean {
    const hash = this.generateMessageHash(config);
    return this.messageHashes.has(hash);
  }

  /**
   * Ajoute un hash de message aux messages actifs
   */
  private addMessageHash(config: ToastConfig): string {
    const hash = this.generateMessageHash(config);
    this.messageHashes.add(hash);
    
    // Nettoyer le hash après la durée du toast
    const duration = config.duration || DEFAULT_DURATIONS[config.type || 'info'];
    if (duration > 0) {
      setTimeout(() => {
        this.messageHashes.delete(hash);
      }, duration + 1000); // Ajouter 1s de marge
    }
    
    return hash;
  }

  /**
   * Supprime un toast actif
   */
  private removeActiveToast(id: string): void {
    const toast = this.activeToasts.get(id);
    if (toast) {
      if (toast.timeoutId) {
        clearTimeout(toast.timeoutId);
      }
      if (toast.dismiss) {
        toast.dismiss();
      }
      this.activeToasts.delete(id);
    }
  }

  /**
   * Affiche un toast avec gestion des doublons
   */
  public show(config: ToastConfig): string | null {
    // Éviter les doublons
    if (this.isDuplicate(config)) {
     //  console.log('Toast dupliqué ignoré:', config.description);
      return null;
    }

    const toastId = config.id || `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const type = config.type || 'info';
    const duration = config.duration || DEFAULT_DURATIONS[type];

    // Ajouter le hash du message
    this.addMessageHash(config);

    try {
      let dismiss: (() => void) | undefined;      // Utiliser Sonner pour les types d'erreur et de warning (plus visibles)
      if (type === 'error' || type === 'warning') {
        const sonnerOptions = {
          id: toastId,
          duration: duration > 0 ? duration : Infinity,
          dismissible: config.dismissible !== false,
          action: config.action ? {
            label: config.action.label,
            onClick: config.action.onClick,
          } : undefined,
        };

        if (type === 'error') {
          const toastIdFromSonner = sonnerToast.error(
            config.title ? `${config.title}: ${config.description}` : config.description,
            sonnerOptions
          );
          dismiss = () => sonnerToast.dismiss(toastIdFromSonner);
        } else {
          const toastIdFromSonner = sonnerToast.warning(
            config.title ? `${config.title}: ${config.description}` : config.description,
            sonnerOptions
          );
          dismiss = () => sonnerToast.dismiss(toastIdFromSonner);
        }      } else {
        // Utiliser Radix Toast pour les autres types (success, info, loading)
        const radixResult = radixToast({
          title: config.title,
          description: config.description,
          variant: type === 'success' ? 'default' : 'default', // Tous les autres types utilisent 'default'
          duration: duration > 0 ? duration : undefined,
        });

        dismiss = radixResult.dismiss;
      }

      // Enregistrer le toast actif
      const timeoutId = duration > 0 ? setTimeout(() => {
        this.removeActiveToast(toastId);
      }, duration) : undefined;

      this.activeToasts.set(toastId, { timeoutId, dismiss });

      return toastId;
    } catch (error) {
      console.error('Erreur lors de l\'affichage du toast:', error);
      return null;
    }
  }

  /**
   * Méthodes de convenance pour chaque type de toast
   */
  public success(description: string, options?: Partial<ToastConfig>): string | null {
    return this.show({
      ...options,
      description,
      type: 'success',
    });
  }

  public error(description: string, options?: Partial<ToastConfig>): string | null {
    return this.show({
      ...options,
      description,
      type: 'error',
    });
  }

  public warning(description: string, options?: Partial<ToastConfig>): string | null {
    return this.show({
      ...options,
      description,
      type: 'warning',
    });
  }

  public info(description: string, options?: Partial<ToastConfig>): string | null {
    return this.show({
      ...options,
      description,
      type: 'info',
    });
  }

  public loading(description: string, options?: Partial<ToastConfig>): string | null {
    return this.show({
      ...options,
      description,
      type: 'loading',
      duration: 0, // Par défaut infini pour les loading
    });
  }

  /**
   * Supprime un toast spécifique
   */
  public dismiss(id: string): void {
    this.removeActiveToast(id);
  }

  /**
   * Supprime tous les toasts actifs
   */
  public dismissAll(): void {
    for (const [id] of this.activeToasts) {
      this.removeActiveToast(id);
    }
    this.activeToasts.clear();
    this.messageHashes.clear();
  }

  /**
   * Supprime tous les toasts d'un type spécifique
   */
  public dismissByType(type: ToastType): void {
    // Cette méthode nécessiterait de stocker le type avec chaque toast actif
    // Pour l'instant, on peut utiliser dismissAll() si nécessaire
    sonnerToast.dismiss();
  }

  /**
   * Met à jour un toast existant
   */
  public update(id: string, config: Partial<ToastConfig>): void {
    const activeToast = this.activeToasts.get(id);
    if (activeToast && config.description) {
      // Pour Sonner, on peut utiliser l'ID pour mettre à jour
      if (config.type === 'error' || config.type === 'warning') {
        sonnerToast.dismiss(id);
        this.show({ ...config, id } as ToastConfig);
      }
      // Pour Radix Toast, c'est plus complexe, on va recréer le toast
    }
  }

  /**
   * Nettoie les resources (à appeler lors du démontage de l'app)
   */
  public cleanup(): void {
    this.dismissAll();
  }
}

// Instance singleton
export const toastManager = new ToastManager();

// Export de méthodes de convenance
export const showToast = (config: ToastConfig) => toastManager.show(config);
export const showSuccess = (description: string, options?: Partial<ToastConfig>) => 
  toastManager.success(description, options);
export const showError = (description: string, options?: Partial<ToastConfig>) => 
  toastManager.error(description, options);
export const showWarning = (description: string, options?: Partial<ToastConfig>) => 
  toastManager.warning(description, options);
export const showInfo = (description: string, options?: Partial<ToastConfig>) => 
  toastManager.info(description, options);
export const showLoading = (description: string, options?: Partial<ToastConfig>) => 
  toastManager.loading(description, options);

export default toastManager;
