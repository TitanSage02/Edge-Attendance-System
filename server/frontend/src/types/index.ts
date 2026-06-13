export * from './authTypes';
export * from './userTypes';
export * from './studentTypes';
export * from './moduleTypes';
export * from './presenceTypes';
export * from './dashboard';
export * from './logTypes';
export * from './alertTypes';

export interface Student {
  id: string;
  firstName: string;
  lastName: string;
  rfidUid?: string | null;
  classGroup: string;
  promotion: string;
  faceEnrolled: boolean;
  rfidEnrolled: boolean;
}

export type ModuleStatus = "online" | "idle" | "offline" | "warning";

export type ModuleType = "rfid" | "camera" | "hybrid" | "entrance" | "classroom" | "other" | "test";

export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: "admin" | "pedagogical" | "technician";
  lastLogin: Date;
  isActive: boolean;
}

export interface Log {
  id: string;
  timestamp: string;
  action: string;
  userId: string;
  userName: string;
  details: string;
  ipAddress: string;
  level: string;
  path: string;
  sessionId: string;
  moduleName: string | null;
}

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

export type { Alert as AlertType };

export type AlertSeverity = "critical" | "moderate" | "minor";

export interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string | Date;
  contextUsed?: number;  // Nombre d'éléments de contexte utilisés par le RAG
  responseTime?: number; // Temps de réponse en millisecondes
}

export interface AttendanceSummary {
  date: string;
  total_students: number;
  present_count: number;
  absent_count: number;
  presence_percentage: number;
  by_class: Record<string, number>;
}

export interface StudentAttendanceStats {
  student_id: string;
  total_days: number;
  present_days: number;
  absent_days: number;
  presence_percentage: number;
  by_module: Record<string, number>;
  by_date: Record<string, boolean>;
}
