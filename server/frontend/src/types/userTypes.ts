export type UserRole = "admin" | "pedagogical" | "technician";

export interface User {
  [x: string]: string | Date | number | boolean | undefined;
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  is_active?: boolean;
  created_at?: string;
  last_login?: string;
}

export interface UserOperationResponse {
  message: string;
  success: boolean;
}