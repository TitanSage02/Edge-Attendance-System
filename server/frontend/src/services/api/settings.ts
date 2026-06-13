import { api } from "../api";
import { AxiosError } from "axios";

// Types pour les paramètres
export interface SystemSettings {
  current_promotion: string;
  notifications_enabled: boolean;
  max_login_attempts: number;
}

export interface BackupSettings {
  auto_backup_enabled: boolean;
  backup_frequency_hours: number;
  max_backup_files: number;
  include_database: boolean;
  include_config: boolean;
  include_logs: boolean;
}

export interface AllSettings {
  system: SystemSettings;
  backup: BackupSettings;
}

export interface SettingsResponse {
  settings: AllSettings;
  last_updated?: string;
  updated_by?: string;
  message: string;
}

export interface SystemInfo {
  current_promotion: string;
  notifications_enabled: boolean;
  last_backup?: string;
  system_health: string;
  version: string;
  database_status?: string;
  mqtt_status?: string;
}

/**
 * Service pour la gestion des paramètres de l'application
 * Communication avec l'API backend /api/v1/settings
 */
export const settingsApi = {
  /**
   * Récupérer tous les paramètres
   */
  getSettings: async (): Promise<SettingsResponse> => {
    try {
      const response = await api.get<SettingsResponse>('/settings/');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération des paramètres");
      }
      throw error;
    }
  },
  /**
   * Mettre à jour tous les paramètres
   */
  updateSettings: async (settings: AllSettings): Promise<SettingsResponse> => {
    try {
      const response = await api.put<SettingsResponse>('/settings/', settings);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la mise à jour des paramètres");
      }
      throw error;
    }
  },

  /**
   * Mettre à jour partiellement les paramètres
   */
  updatePartialSettings: async (updates: Partial<AllSettings>): Promise<SettingsResponse> => {
    try {
      const response = await api.patch<SettingsResponse>('/settings/', updates);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la mise à jour des paramètres");
      }
      throw error;
    }
  },

  /**
   * Remettre les paramètres aux valeurs par défaut
   */
  resetToDefaults: async (): Promise<SettingsResponse> => {
    try {
      const response = await api.post<SettingsResponse>('/settings/reset');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la remise à zéro des paramètres");
      }
      throw error;
    }
  },

  /**
   * Récupérer les informations système
   */
  getSystemInfo: async (): Promise<SystemInfo> => {
    try {
      const response = await api.get<SystemInfo>('/settings/system-info');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération des informations système");
      }
      throw error;
    }
  },
  /**
   * Crée une sauvegarde système complète
   */
  createBackup: async (): Promise<any> => {
    try {
      const response = await api.post<any>('/settings/backup');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la création de sauvegarde système");
      }
      throw error;
    }
  },

  /**
   * Liste les sauvegardes système disponibles
   */
  listBackups: async (): Promise<any[]> => {
    try {
      const response = await api.get<any[]>('/settings/backup');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la liste des sauvegardes système");
      }
      throw error;
    }
  },

  /**
   * Restaure une sauvegarde système
   */
  restoreBackup: async (backupName: string): Promise<any> => {
    try {
      const response = await api.post<any>(`/settings/backup/${encodeURIComponent(backupName)}/restore`);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la restauration système");
      }
      throw error;
    }
  },
};
