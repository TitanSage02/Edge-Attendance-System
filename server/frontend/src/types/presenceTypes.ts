export interface Student {
    id: string;
    firstName: string;
    lastName: string;
    classGroup: string;
}

export interface Attendance {
    id: number;
    student_id: string;
    status: boolean;
    module_uid: number;
    timestamp: string;
    entry_time?: string;
    exit_time?: string;
    student?: Student;
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

export interface StudentPresenceStats {
    student_id: string;
    student_name: string;
    present_count: number;
    total_sessions: number;
    percentage: number;
}

export interface PresenceSummary {
    date: string; 
    total_students: number;
    present_count: number;
    absent_count: number;
    presence_percentage: number;
    by_class?: Record<string, number>; 
    students?: StudentPresenceStats[];
}

export interface PresenceRecord {
    id: number;
    student_id: string;
    status: boolean;
    module_uid: number;
    timestamp: string; 
} 