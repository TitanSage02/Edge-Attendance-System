export interface Alert {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  details: string;
  timestamp: string;
  source: string;
  moduleId?: string;
  studentId?: string;
  resolved: boolean;
  moduleName?: string;
}

export type AlertType = "auth_failure" | "module_offline" | "temperature" | "system";
export type AlertSeverity = "critical" | "warning" | "info"; 