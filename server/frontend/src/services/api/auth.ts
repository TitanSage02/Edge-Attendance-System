import { api } from "../api";
import { User } from "@/types/userTypes";
import {
  LoginCredentials,
  LoginResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  ChangePasswordRequest,
  ChangePasswordResponse,
  UpdateProfileResponse,
} from "@/types/authTypes";

/*
 * Service Auth – adapté à l'API FastAPI (prefixe /api/v1 déjà dans api.ts)
 * Les endpoints réels sont donc :
 *   POST   /auth/login
 *   POST   /auth/logout
 *   POST   /auth/reset-password
 *   POST   /auth/reset-password/confirm
 *   GET    /auth/me
 *   PUT    /auth/me
 */

export const authApi = {
  /* --------------------------------------------------------------------- */
  /* Login                                                                 */
  /* --------------------------------------------------------------------- */
  login: async (creds: LoginCredentials): Promise<LoginResponse> => {
    const { rememberMe, ...rest } = creds as any;
    const payload = rememberMe !== undefined ? { ...rest, remember_me: rememberMe } : rest;
    
    const { data } = await api.post<LoginResponse>("/auth/login", payload);
    
    return data;
  },

  /* --------------------------------------------------------------------- */
  /* Logout – backend invalide le refresh cookie                            */
  /* --------------------------------------------------------------------- */
  logout: async (): Promise<void> => {
    await api.post("/auth/logout");
  },

  /* --------------------------------------------------------------------- */
  /* Password reset workflow                                                */
  /* --------------------------------------------------------------------- */
  requestPasswordReset: async (data: ResetPasswordRequest): Promise<ResetPasswordResponse> => {
    const { data: resp } = await api.post<ResetPasswordResponse>(
      "/auth/reset-password",
      data,
    );
    return resp;
  },

  /* --------------------------------------------------------------------- */
  /* Profil courant                                                         */
  /* --------------------------------------------------------------------- */
  /*
   * Récupère le profil de l'utilisateur courant
   * @returns {Promise<User>} Le profil de l'utilisateur courant
   */
  getCurrentUser: async (): Promise<User> => {
    const { data } = await api.get<User>("/auth/profile");
    return data;
  },  
  updateProfile: async (changes: Partial<User>): Promise<UpdateProfileResponse> => {
    const { data } = await api.patch<User>("/auth/profile", changes);
    return { user: data };
  },
  /* --------------------------------------------------------------------- */
  /* Password change workflow                                              */
  /* --------------------------------------------------------------------- */
  changePassword: async (data : ChangePasswordRequest): Promise<ChangePasswordResponse> => {
    const payload = {
      old_password: data.currentPassword,
      new_password: data.newPassword
    };
    const { data: resp } = await api.post<ChangePasswordResponse>("/auth/change-password", payload);
    return resp;
  },
};