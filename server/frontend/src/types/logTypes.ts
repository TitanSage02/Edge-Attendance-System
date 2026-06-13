// Type pour les messages WebSocket, correspondant à LogRead du backend
export interface WebSocketLog {
    id: number; // Backend envoie int
    timestamp: string; // ou Date, à convertir depuis la chaîne ISO datetime
    level: string; // Ex: "INFO", "WARNING", "ERROR", "CRITICAL"
    message: string; // Anciennement 'action'
    source: string; // Nouvelle propriété, ex: "module_x", "api", "system"
    module_uid?: number | null; // Anciennement moduleId, type string
    user_id?: number | null; // Anciennement userId, type string
    details?: Record<string, any> | null; // Anciennement string, maintenant Record<string, any> | null
}

// L'ancien type Log peut être conservé s'il est utilisé ailleurs pour des logs enrichis,
// ou il peut être supprimé/remplacé si WebSocketLog est le seul type de log nécessaire.
// Pour l'instant, je commente l'ancien et nous pourrons décider plus tard.
/*
export interface Log {
    id: string;
    timestamp: Date;
    action: string;
    userId: string;
    userName: string;
    details: string;
    ipAddress?: string;
    userAgent?: string;
    level: "info" | "warning" | "error";
    path?: string;
    moduleName?: string;
    sessionId?: string;
    moduleId?: string;
}
*/
  