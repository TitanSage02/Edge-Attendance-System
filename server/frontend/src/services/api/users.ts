import { api } from "../api";
import { User } from '@/types/userTypes';

/**
 * Service pour la gestion des utilisateurs (CRUD)
 * Communication avec le backend pour l'administration des utilisateurs
 */
export const usersApi = {
  /**
   * Récupérer la liste des utilisateurs
   */
  getUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/v1/users/');
    return response.data;
  },

  /**
   * Créer un nouvel utilisateur
   * @param data Données de l'utilisateur
   */
  createUser: async (data: Partial<User>): Promise<User> => {
    const response = await api.post<User>('/v1/users/', data);
    return response.data;
  },

  /**
   * Mettre à jour un utilisateur
   * @param id ID de l'utilisateur
   * @param data Données mises à jour
   */
  updateUser: async (id: string, data: Partial<User>): Promise<User> => {
    const response = await api.patch<User>(`/v1/users/${id}`, data);
    return response.data;
  },

  /**
   * Supprimer un utilisateur
   * @param id ID de l'utilisateur
   */
  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/v1/users/${id}`);
  },
};
