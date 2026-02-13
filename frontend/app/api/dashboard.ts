// Dashboard API functions
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

export interface DashboardAnalytics {
  total_users: number;
  active_workflows: number;
  completed_projects: number;
  pending_assignments: number;
}

export const dashboardApi = {
  getAnalytics: async (): Promise<DashboardAnalytics> => {
    return apiCall<DashboardAnalytics>(API_ENDPOINTS.DASHBOARD_ANALYTICS, {
      method: "GET",
    });
  },
};
