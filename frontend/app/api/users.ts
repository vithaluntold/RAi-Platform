// User API functions
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";
import { User, UserCreateRequest } from "@/types/user";

export const userApi = {
  getUsers: async (): Promise<User[]> => {
    return apiCall<User[]>(API_ENDPOINTS.USERS, {
      method: "GET",
    });
  },

  getUser: async (id: string): Promise<User> => {
    return apiCall<User>(API_ENDPOINTS.USER(id), {
      method: "GET",
    });
  },

  createUser: async (user: UserCreateRequest): Promise<User> => {
    return apiCall<User>(API_ENDPOINTS.USERS, {
      method: "POST",
      body: JSON.stringify(user),
    });
  },

  createMultipleUsers: async (users: UserCreateRequest[]): Promise<unknown> => {
    return apiCall(API_ENDPOINTS.USERS, {
      method: "POST",
      body: JSON.stringify(users),
    });
  },

  updateUser: async (id: string, user: Partial<User>): Promise<User> => {
    return apiCall<User>(API_ENDPOINTS.USER(id), {
      method: "PUT",
      body: JSON.stringify(user),
    });
  },

  deleteUser: async (id: string): Promise<void> => {
    await apiCall(API_ENDPOINTS.USER(id), {
      method: "DELETE",
    });
  },
};
