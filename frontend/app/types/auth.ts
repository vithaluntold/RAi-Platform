// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: Record<string, unknown> | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}
