import { api } from "@/services/api/api";
import { AxiosError } from "axios";
import { User, UserRole } from "@/types/userTypes";

export interface CreateUserPayload {
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
}

export const userApi = {
  /**
   * Récupérer la liste des utilisateurs
   */
  getUsers: async (): Promise<User[]> => {
    try {
      const response = await api.get('/users/');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération des utilisateurs");
      }
      throw error;
    }
  },

  /**
   * Créer un nouvel utilisateur
   */
  createUser: async (userData: CreateUserPayload): Promise<User> => {
    try {
      const response = await api.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la création de l'utilisateur");
      }
      throw error;
    }
  },

  /**
   * Mettre à jour un utilisateur
   */
  updateUser: async (userId: string, userData: Partial<CreateUserPayload>): Promise<User> => {
    try {
      const response = await api.patch(`/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la mise à jour de l'utilisateur");
      }
      throw error;
    }
  },

  /**
   * Supprimer un utilisateur
   */
  deleteUser: async (userId: string): Promise<void> => {
    try {
      await api.delete(`/users/${userId}`);
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la suppression de l'utilisateur");
      }
      throw error;
    }
  }
};