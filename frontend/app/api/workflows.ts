// Workflow API functions
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";
import { Workflow } from "@/types/workflow";

export const workflowApi = {
  getWorkflows: async (): Promise<Workflow[]> => {
    return apiCall<Workflow[]>(API_ENDPOINTS.WORKFLOWS, {
      method: "GET",
    });
  },

  getWorkflow: async (id: string): Promise<Workflow> => {
    return apiCall<Workflow>(API_ENDPOINTS.WORKFLOW(id), {
      method: "GET",
    });
  },

  createWorkflow: async (workflow: Partial<Workflow>): Promise<Workflow> => {
    return apiCall<Workflow>(API_ENDPOINTS.WORKFLOWS, {
      method: "POST",
      body: JSON.stringify(workflow),
    });
  },

  updateWorkflow: async (id: string, workflow: Partial<Workflow>): Promise<Workflow> => {
    return apiCall<Workflow>(API_ENDPOINTS.WORKFLOW(id), {
      method: "PUT",
      body: JSON.stringify(workflow),
    });
  },

  deleteWorkflow: async (id: string): Promise<void> => {
    await apiCall(API_ENDPOINTS.WORKFLOW(id), {
      method: "DELETE",
    });
  },
};
