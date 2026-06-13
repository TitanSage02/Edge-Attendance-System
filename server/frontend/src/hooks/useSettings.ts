import { useState, useEffect } from 'react';
import { settingsApi, AllSettings, SystemInfo } from '@/services/api/settings';
import { useUnifiedToast } from '@/hooks/useUnifiedToast';

// Event bus pour la synchronisation de la promotion
export const PROMOTION_UPDATED_EVENT = 'settings:promotion_updated';

export interface Backup {
  name: string;
  size: number;
  created_at: string;
  created_by: string;
  backup_type: string;
  includes: {
    database: boolean;
    config: boolean;
    logs: boolean;
  };
  path: string;
}

export interface UseSettingsReturn {
  // Existing properties
  settings: AllSettings | null;
  systemInfo: SystemInfo | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  lastUpdated: string | null;
  updatedBy: string | null;
  
  // Actions
  refreshSettings: () => Promise<void>;
  updateSettings: (settings: AllSettings) => Promise<void>;
  updatePartialSettings: (updates: Partial<AllSettings>) => Promise<void>;
  resetToDefaults: () => Promise<void>;
  refreshSystemInfo: () => Promise<void>;
  
  // Backup functions
  backups: Backup[];
  loadingBackups: boolean;
  createBackup: () => Promise<any>;
  listBackups: () => Promise<any[]>;
  restoreBackup: (backupName: string) => Promise<any>;
}

/**
 * Hook pour la gestion des paramètres de l'application
 */
export const useSettings = (): UseSettingsReturn => {
  const [settings, setSettings] = useState<AllSettings | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [updatedBy, setUpdatedBy] = useState<string | null>(null);
  
  // Backup states
  const [backups, setBackups] = useState<Backup[]>([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  
  const { success, error: showError } = useUnifiedToast();

  // Chargement initial des paramètres
  const refreshSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await settingsApi.getSettings();
      setSettings(response.settings);
      setLastUpdated(response.last_updated || null);
      setUpdatedBy(response.updated_by || null);
        } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors du chargement des paramètres';
      setError(errorMessage);
      showError(errorMessage, { title: "Erreur" });
    } finally {
      setLoading(false);
    }
  };
  // Chargement des informations système
  const refreshSystemInfo = async () => {
    try {
      const info = await settingsApi.getSystemInfo();
      setSystemInfo(info);
    } catch (err) {
      console.error('Erreur lors du chargement des informations système:', err);
      // En cas d'erreur, on peut quand même garder les anciennes données
      // plutôt que de mettre null
    }
  };

  // Mise à jour complète des paramètres
  const updateSettings = async (newSettings: AllSettings) => {
    try {
      setSaving(true);
      setError(null);
        const response = await settingsApi.updateSettings(newSettings);
      setSettings(response.settings);
      setLastUpdated(response.last_updated || null);
      setUpdatedBy(response.updated_by || null);
      
      success(response.message || "Paramètres mis à jour avec succès", { title: "Succès" });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la mise à jour';
      setError(errorMessage);
      showError(errorMessage, { title: "Erreur" });
    } finally {
      setSaving(false);
    }
  };
  // Mise à jour partielle des paramètres
  const updatePartialSettings = async (updates: Partial<AllSettings>) => {
    try {
      setSaving(true);
      setError(null);
      const response = await settingsApi.updatePartialSettings(updates);
      setSettings(response.settings);
      setLastUpdated(response.last_updated || null);
      setUpdatedBy(response.updated_by || null);
      
      // Vérifier si la promotion a été mise à jour
      if (updates.system?.current_promotion) {
        // Émettre un événement pour notifier que la promotion a été mise à jour
        window.dispatchEvent(new CustomEvent(PROMOTION_UPDATED_EVENT, {
          detail: { promotion: updates.system.current_promotion }
        }));
      }
      
      success(response.message || "Paramètres mis à jour avec succès", { title: "Succès" });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la mise à jour';
      setError(errorMessage);
      showError(errorMessage, { title: "Erreur" });
    } finally {
      setSaving(false);
    }
  };

  // Remise à zéro des paramètres
  const resetToDefaults = async () => {
    try {
      setSaving(true);
      setError(null);
        const response = await settingsApi.resetToDefaults();
      setSettings(response.settings);
      setLastUpdated(response.last_updated || null);
      setUpdatedBy(response.updated_by || null);
      
      success(response.message || "Paramètres remis aux valeurs par défaut", { title: "Succès" });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la remise à zéro';
      setError(errorMessage);
      showError(errorMessage, { title: "Erreur" });
    } finally {
      setSaving(false);
    }  };

  // Gestion des sauvegardes
  const createBackup = async () => {
    try {
      setSaving(true);
      setError(null);
      const result = await settingsApi.createBackup();
      success("Sauvegarde système créée avec succès", { title: "Succès" });
      await listBackups();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erreur lors de la création de sauvegarde système";
      setError(errorMessage);
      showError(errorMessage, { title: "Erreur" });
    } finally {
      setSaving(false);
    }
  };

  const listBackups = async () => {
    try {
      setLoadingBackups(true);
      const result = await settingsApi.listBackups();
      setBackups(result || []);
      return result;
    } catch (err) {      const errorMessage = err instanceof Error ? err.message : "Erreur lors de la liste des sauvegardes système";
      console.error(errorMessage);
      setBackups([]);
    } finally {
      setLoadingBackups(false);
    }
  };

  const restoreBackup = async (backupName: string) => {
    try {
      setSaving(true);
      setError(null);
      const result = await settingsApi.restoreBackup(backupName);
      success("Restauration système effectuée avec succès", { title: "Succès" });
      await refreshSettings();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erreur lors de la restauration système";
      setError(errorMessage);
      showError(errorMessage, { title: "Erreur" });
    } finally {
      setSaving(false);
    }
  };

  // Chargement initial
  useEffect(() => {
    refreshSettings();
    refreshSystemInfo();
    listBackups();
  }, []);

  return {
    settings,
    systemInfo,
    loading,
    saving,
    error,
    lastUpdated,
    updatedBy,
    refreshSettings,
    updateSettings,
    updatePartialSettings,
    resetToDefaults,
    refreshSystemInfo,
    // Backup functions
    backups,
    loadingBackups,
    createBackup,
    listBackups,
    restoreBackup,
  };
};
