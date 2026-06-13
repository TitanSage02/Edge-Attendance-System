import { api } from "../api";
import { Attendance, AttendanceSummary, StudentAttendanceStats } from "@/types/presenceTypes";
import { AxiosError } from "axios";

export type { Attendance, AttendanceSummary, StudentAttendanceStats };

interface AttendanceResponse {
  data: Attendance[];
  total: number;
}

interface AddAttendanceParams {
  student_id: string;
  module_uid: number;
  status: boolean;
  timestamp: string;
}

/**
 * Service pour la gestion des présences
 * Communication avec l'API backend /api/v1/presence.py
 */
export const presenceApi = {
  /**
   * Récupérer la liste des classes
   */
  getClasses: async (): Promise<{ id: string; name: string }[]> => {
    try {
      const response = await api.get('/classes/');
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération des classes");
      }
      throw error;
    }
  },

  /**
   * Récupérer l'historique des présences
   * @param params Filtres et pagination
   */
  getAttendance: async (params?: {
    skip?: number;
    limit?: number;
    student_id?: string;
    module_uid?: number;
    date_from?: string;
    date_to?: string;
    status?: boolean;
    class_group?: string;
  }): Promise<Attendance[]> => {
    try {
      const response = await api.get('/presences', { params });
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response?.status === 404) {
          return [];
        }
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération des présences");
      }
      throw error;
    }
  },

  /**
   * Récupérer le résumé des présences pour une date
   * @param params Filtres de date et de classe
   */
  getDailySummary: async (params: {
    target_date: string;
    class_group?: string;
  }): Promise<AttendanceSummary> => {
    try {
      const response = await api.get('/presences/summary', { params });
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération du résumé des présences");
      }
      throw error;
    }
  },

  /**
   * Récupérer les statistiques de présence d'un étudiant
   * @param studentId ID de l'étudiant
   * @param params Filtres de date
   */
  getStudentStats: async (
    studentId: string,
    params?: {
      date_from?: string;
      date_to?: string;
      module_uid?: number;
    }
  ): Promise<StudentAttendanceStats> => {
    try {
      const response = await api.get(`/presences/student/${studentId}/stats`, { params });
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la récupération des statistiques de l'étudiant");
      }
      throw error;
    }
  },

  /**
   * Enregistrer manuellement une présence
   * @param data Données de présence
   */
  addAttendance: async (params: AddAttendanceParams): Promise<Attendance> => {
    try {
      const response = await api.post('/presences', params);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        const errorMessage = error.response?.data?.detail || "Erreur lors de l'enregistrement de la présence";
        if (error.response?.status === 409) {
          throw new Error("L'étudiant a déjà une présence enregistrée pour ce module dans les 5 dernières minutes");
        }
        throw new Error(errorMessage);
      }
      throw error;
    }
  },

  /**
   * Mettre à jour une présence
   * @param id ID de la présence
   * @param data Données mises à jour
   */
  updateAttendance: async (id: string, data: { 
    status?: boolean;
    timestamp?: string;
  }): Promise<Attendance> => {
    try {
      const response = await api.patch(`/presences/${id}`, data);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de la mise à jour de la présence");
      }
      throw error;
    }
  },

  /**
   * Exporter les présences
   * @param params Filtres de date et de classe
   */
  exportPresences: async (params: {
    target_date: string;
    class_group?: string;
  }): Promise<Blob> => {
    try {
      const response = await api.get('/presences/export', { 
        params,
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError) {
        throw new Error(error.response?.data?.detail || "Erreur lors de l'exportation des présences");
      }
      throw error;
    }
  },
};
