import { api } from "../api";

export interface FaceEnrollmentResponse {
  student_id: string;
  message: string;
}

/**
 * Service pour l'enrôlement facial - upload et traitement des photos
 */
export const faceEnrollmentApi = {
  /**
   * Upload des 6 photos d'enrôlement facial pour un étudiant
   * @param studentId ID de l'étudiant
   * @param photos Liste des 6 photos sous forme de Blob
   */
  uploadEnrollmentPhotos: async (
    studentId: string, 
    photos: Blob[]
  ): Promise<FaceEnrollmentResponse> => {
    if (photos.length !== 6) {
      throw new Error("Exactement 6 photos sont requises pour l'enrôlement");
    }

    const formData = new FormData();
    
    // Ajouter chaque photo au FormData
    photos.forEach((photo, index) => {
      formData.append('photos', photo, `${studentId}_photo_${index + 1}.jpg`);
    });

    try {
      const response = await api.post<FaceEnrollmentResponse>(
        `/embeddings/face-enrollment/${studentId}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000, // 60 secondes
        }
      );

      return response.data;
    } catch (error: any) {
      // Gestion des erreurs spécifiques
      if (error.response?.status === 400) {
        throw new Error(error.response.data.detail || "Données invalides pour l'enrôlement");
      } else if (error.response?.status === 404) {
        throw new Error("Étudiant non trouvé");
      } else if (error.response?.status === 413) {
        throw new Error("Les photos sont trop volumineuses");
      } else if (error.response?.status === 500) {
        throw new Error("Erreur serveur lors du traitement des photos");
      } else {
        throw new Error("Erreur réseau lors de l'upload des photos");
      }
    }
  },
};
