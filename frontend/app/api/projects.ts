// Project API functions
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";
import { Project } from "@/types/project";

export const projectApi = {
  getProjects: async (): Promise<Project[]> => {
    return apiCall<Project[]>(API_ENDPOINTS.PROJECTS, {
      method: "GET",
    });
  },

  getProject: async (id: string): Promise<Project> => {
    return apiCall<Project>(API_ENDPOINTS.PROJECT(id), {
      method: "GET",
    });
  },

  createProject: async (project: Partial<Project>): Promise<Project> => {
    return apiCall<Project>(API_ENDPOINTS.PROJECTS, {
      method: "POST",
      body: JSON.stringify(project),
    });
  },

  updateProject: async (id: string, project: Partial<Project>): Promise<Project> => {
    return apiCall<Project>(API_ENDPOINTS.PROJECT(id), {
      method: "PUT",
      body: JSON.stringify(project),
    });
  },

  deleteProject: async (id: string): Promise<void> => {
    await apiCall(API_ENDPOINTS.PROJECT(id), {
      method: "DELETE",
    });
  },
};
