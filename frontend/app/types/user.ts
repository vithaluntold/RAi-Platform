// User-related types
export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  auth_provider: AuthProvider;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  ADMIN = "admin",
  WORKER = "worker",
  CLIENT = "client",
}

export enum AuthProvider {
  LOCAL = "local",
  KEYCLOAK_AD = "keycloak_ad",
}

export interface UserCreateRequest {
  email: string;
  first_name: string;
  last_name: string;
  password?: string;
  role?: UserRole;
}
