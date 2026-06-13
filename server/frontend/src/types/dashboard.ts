// src/types/dashboard.ts

// Définition pour une seule entrée de log pour le tableau de bord
export interface DashboardLogEntry {
  id: number;
  timestamp: string;
  level: string;
  action: string;
  details: string | null;
  userName: string | null;
  moduleName: string | null;
}

export interface DashboardMetrics {
    todayAttendance: {
      total: number;
      byClass: { name: string; present: number; absent: number }[];
    };
    alerts: {
      total: number;
    };
    modules: {
      total: number;
      online: number;
      offline: number;
      standby: number;
    };
    recentLogs: DashboardLogEntry[]; // Utilisation du nouveau type
  }
  