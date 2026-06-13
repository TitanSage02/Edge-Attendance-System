import { api } from "@/services/api";
import type { DashboardMetrics } from "@/types/dashboard";

export const dashboardApi = {
  getMetrics: async (): Promise<DashboardMetrics> => {
    const { data } = await api.get<DashboardMetrics>("/dashboard/metrics");
    return data;
  },
};