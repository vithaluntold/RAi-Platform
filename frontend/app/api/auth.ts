// Authentication API functions
import { apiCall, setAuthToken, clearAuthToken } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";
import { LoginRequest, TokenResponse } from "@/types/auth";

export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const result = await apiCall<TokenResponse>(
      API_ENDPOINTS.LOGIN,
      {
        method: "POST",
        body: JSON.stringify(credentials),
      }
    );
    setAuthToken(result.access_token);
    return result;
  },

  logout: async (): Promise<void> => {
    clearAuthToken();
    try {
      await apiCall(API_ENDPOINTS.LOGOUT, {
        method: "POST",
      });
    } catch {
      // Logout on client side is already done
      console.log("Logout API call failed, but token cleared locally");
    }
  },

  refreshToken: async (): Promise<TokenResponse> => {
    const result = await apiCall<TokenResponse>(
      API_ENDPOINTS.REFRESH,
      {
        method: "POST",
      }
    );
    setAuthToken(result.access_token);
    return result;
  },
};
