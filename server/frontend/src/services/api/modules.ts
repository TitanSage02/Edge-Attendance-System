import { api } from "../api";
import { Module } from '@/types/moduleTypes';

/**
 * Service pour la gestion des modules (CRUD)
 * Communication avec l'API backend /api/v1/modules.py
 */
export const modulesApi = {
  /**
   * Récupérer la liste des modules
   * @param params Filtres optionnels
   */
  getModules: async (params?: { 
                status?: string; 
                type?: string 
              }): Promise<Module[]> => {
                const response = await api.get<Module[]>('/modules/', { params });
                return response.data;
              },
  
  /**
   * Récupérer un module par son ID
   * @param id ID du module
   */
  getModule: async (id: number): Promise<Module> => {
              const response = await api.get<Module>(`/modules/${id}`);
              return response.data;
            },

  /**
   * Créer un nouveau module
   * @param data Données du module
   */
  createModule: async (data: Partial<Module>): Promise<Module> => {
                  const response = await api.post<Module>('/modules/', data);
                  return response.data;
                },

  /**
   * Mettre à jour un module
   * @param id ID du module
   * @param data Données mises à jour
   */
  updateModule: async (id: number, data: Partial<Module>): Promise<Module> => {
                  const response = await api.patch<Module>(`/modules/${id}`, data);
                  return response.data;
                },

  /**
   * Supprimer un module
   * @param id ID du module
   */
  deleteModule: async (id: number): Promise<void> => {
                  await api.delete(`/modules/${id}`);
                },

  /**
   * Obtenir l'état actuel d'un module
   * @param id ID du module
   */
  getModuleStatus: async (id: number): Promise<{ status: string; temperature: number }> => {
                      const response = await api.get<{ status: string; temperature: number }>(`/modules/${id}/status`);
                      return response.data;
                    },

  /**
   * Redémarrer un module
   * @param id ID du module
   * @returns Confirmation de la demande de redémarrage
   */
  restartModule: async (id: number): Promise<{ message: string; requestId: string }> => {
                    const response = await api.post<{ message: string; requestId: string }>(`/modules/${id}/restart`);
                    return response.data;
                  }
};
