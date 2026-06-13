export type ModuleStatus = "online" | "idle" | "offline" | "warning";

export type ModuleType = "rfid" | "camera" | "hybrid" | "entrance" | "classroom" | "other" | "test";

export interface Module {
  uid: number;
  name: string;
  description?: string;
  emplacement?: string;
  faceChecked: boolean;
  rfidChecked: boolean;
  created_by?: string;
  updated_by?: string;
  status: ModuleStatus;
  uptime?: string;
  last_seen?: string; // Date de dernière activité au format ISO
}

// Nouvelle interface pour les messages WebSocket, correspondant à ModuleStatusRead du backend
export interface WebSocketModuleStatus {
  id: number; // id de l'enregistrement de statut
  module_uid: number; // UID du module
  status: string; // Peut être plus large que ModuleStatus, ex: "online", "offline", "error", "updating"
  version?: string | null;
  uptime?: number | null; // Backend envoie float, JS number
  memory_usage?: number | null; // Backend envoie float, JS number
  cpu_usage?: number | null; // Backend envoie float, JS number
  details?: Record<string, any> | null;
  last_seen: string; // ou Date, à convertir depuis la chaîne ISO datetime
}
