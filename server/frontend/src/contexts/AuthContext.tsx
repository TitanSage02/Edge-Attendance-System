/**
 * AuthContext.tsx 
 * ---------------------------------------------------------------------------
 * Branche l'auth frontend sur FastAPI via l'instance Axios partagée (api.ts)
 * – Le cookie *refresh* reste HttpOnly ; 
 * l'intercepteur global dans api.ts s'occupe du /auth/refresh et du re‑jeu de requêtes.
 * – Ici on gère seulement la persistance du JWT (access‑token) et l'état UI.
 * ---------------------------------------------------------------------------
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useReducer,
  ReactNode,
} from "react";
import { toastManager } from "@/services/toastManager";
import { websocketService } from "@/services/websocket";

import { api } from "@/services/api";           // instance centralisée avec refresh
import { authApi } from "@/services/api/auth";  // wrapper d'endpoints auth

import {
  LoginCredentials,
  AuthState,
  LoginResponse,
  ResetPasswordResponse,
  UpdateProfileResponse,
} from "@/types/authTypes";
import { User, UserRole } from "@/types/userTypes";

/* ---------------------------------------------------------------------------
 * Actions / reducer
 * ------------------------------------------------------------------------- */

type AuthAction =
  | { type: "LOGIN_START" }
  | { type: "LOGIN_SUCCESS"; payload: { user: User; token: string } }
  | { type: "LOGIN_ERROR" }
  | { type: "LOGOUT" }
  | { type: "UPDATE_PROFILE"; payload: Partial<User> };

const initialState: AuthState = {
  user: null,
  token: null,
  loading: false,
  error: null,
  isAuthenticated: false,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "LOGIN_START":
      return { ...state, loading: true, error: null };
    
    case "LOGIN_SUCCESS":
      return { ...state, ...action.payload, loading: false, isAuthenticated: true };
    
    case "LOGIN_ERROR":
      return { ...state, loading: false, error: "Adresse e-mail ou mot de passe incorrect." };
      
    case "LOGOUT":
      return initialState;
    
    case "UPDATE_PROFILE":
      return state.user ? { ...state, user: { ...state.user, ...action.payload } } : state;
    
    default:
      return state;
  }
}


/* ---------------------------------------------------------------------------
 * Contexte
 * ------------------------------------------------------------------------- */

interface AuthContextType extends AuthState {
  login: (c: LoginCredentials) => Promise<LoginResponse>;
  logout: () => void;
  requestPasswordReset: (email: string) => Promise<ResetPasswordResponse>;
  updateProfile: (data: { firstName: string, lastName: string, email: string }) => Promise<UpdateProfileResponse>;
  hasRole: (r: UserRole | UserRole[]) => boolean;
  clearError: () => void;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

/* ---------------------------------------------------------------------------
 * Provider
 * ------------------------------------------------------------------------- */

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  /* -- Hydrate depuis storage --------------------------------------------- */
  useEffect(() => {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const userRaw = localStorage.getItem("user") || sessionStorage.getItem("user");
   
    if (token && userRaw) {
      try {
        const parsedUser = JSON.parse(userRaw);
       //  console.log("User hydraté du storage:", parsedUser);
       //  console.log("User role:", parsedUser.role);
        
        api.defaults.headers.common["Authorization"] = `Bearer ${token}`; // Ajout de l'en-tête d'autorisation
        dispatch({ type: "LOGIN_SUCCESS", payload: { token, user: parsedUser } });
        
        // Initialiser la connexion WebSocket avec le token
        console.log("🔌 Initialisation WebSocket avec token existant");
        websocketService.connect(token);
      } catch (error) {
        // console.error("Erreur lors de l'hydratation de l'utilisateur:", error);
        localStorage.removeItem("user");
        sessionStorage.removeItem("user");
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
      }
    }
  }, []);

  /* --------------------------------------------------------------------- */
  /* Connexion                                                             */
  /* --------------------------------------------------------------------- */
  const login = async ({ email, password, rememberMe }: LoginCredentials): Promise<LoginResponse> => {
    dispatch({ type: "LOGIN_START" });   
    try {
      const res = await authApi.login({ email, password, rememberMe }); 
      // // Vérifier si le compte est explicitement désactivé (is_active === false)
      // // Si is_active est undefined, on considère que le compte est actif par défaut
      // if (res.user.is_active === false) throw new Error("Votre compte est désactivé. Veuillez contacter l'administrateur.");

      persistAuth(res.user, res.token, rememberMe);
        
      api.defaults.headers.common["Authorization"] = `Bearer ${res.token}`;
      dispatch({ type: "LOGIN_SUCCESS", payload: res });
      
      // Initialiser la connexion WebSocket après le login
      console.log("🔌 Initialisation WebSocket après login");
      websocketService.connect(res.token);
        
      // toastManager.success("Connexion réussie");
      return res;
    } catch {
      dispatch({ type : "LOGIN_ERROR" });
      // toastManager.success("Adresse e-mail ou mot de passe incorrect");
    }

  };

  /* -- Persistance -------------------------------------------------------- */
  const persistAuth = (user: User, token: string, remember: boolean) => {
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem("token", token);
    storage.setItem("user", JSON.stringify(user));
  };

  /* -- Déconnexion -------------------------------------------------------- */
  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      // Déconnecter le WebSocket
      console.log("🔌 Déconnexion WebSocket lors du logout");
      websocketService.disconnect();
      
      localStorage.clear();
      sessionStorage.clear();
      delete api.defaults.headers.common["Authorization"];
      dispatch({ type: "LOGOUT" });
    }
  };

  /* -- Mise à jour profil ------------------------------------------------- */
  const updateProfile = async (data: { firstName: string, lastName: string, email: string } ): Promise<UpdateProfileResponse> => {
    if (!state.user) throw new Error("Utilisateur non authentifié");
    try {
      const payload = {
        role: state.user.role,
        ...data, // Inclure les champs à mettre à jour
      };
      
      const updated = await authApi.updateProfile(payload);

      persistAuth(updated.user, state.token || "", true);
      dispatch({ type: "UPDATE_PROFILE", payload: data });

      toastManager.success("Profil mis à jour");
      
      return { user: updated.user };
    } catch {
      /*  */
    }
  };

  /* -- Helpers ------------------------------------------------------------ */
  const requestPasswordReset = (email: string) => authApi.requestPasswordReset({ email });
  const hasRole = (roles: UserRole | UserRole[]) => {
    if (!state.user) {
     //  console.log("hasRole: Aucun utilisateur dans le state");
      return false;
    }
    
   //  console.log("hasRole: Vérification pour", roles, "contre", state.user.role);
    
    const result = Array.isArray(roles) 
      ? roles.includes(state.user.role) 
      : state.user.role === roles;
    
   //  console.log("hasRole: Résultat =", result);
    return result;
  };

  const clearError = () => dispatch({ type: "LOGIN_ERROR" });

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        requestPasswordReset,
        updateProfile,
        hasRole,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

/* ---------------------------------------------------------------------------
 * Hook personnalisé
 * ------------------------------------------------------------------------- */

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth doit être utilisé dans un AuthProvider");
  }
  return context;
};
