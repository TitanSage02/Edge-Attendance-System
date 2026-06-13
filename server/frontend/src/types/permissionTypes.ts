export interface Permission {
  name: string;
  description: string;
}

export interface RolePermissions {
  admin: Permission[];
  pedagogical: Permission[];
  technician: Permission[];
} 