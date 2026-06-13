import { useState, useEffect } from 'react';
import { websocketService } from './index';
import { Log, Module } from '@/types'; //

/**
 * Hook pour les données en temps réel du tableau de bord
 * Se connecte via WebSocket pour recevoir les mises à jour
 */
export const useDashboardRealtime = () => {
  const [realtimeLogs, setRealtimeLogs] = useState<Log[]>([]);

  const [alerts, setAlerts] = useState<{
      total: number; 
      moderate: number;
      critical: number;
      minor: number;
    }>({ 
        total: 0, 
        critical: 0, 
        moderate: 0, 
        minor: 0 
      });

  const [moduleStatus, setModuleStatus] = useState<{
      total: number;
      online: number;
      offline: number;
      warning: number;
      standby: number;
      temperature: number;
    }>({
        total: 0,
        online: 0,
        offline: 0,
        warning: 0,
        standby: 0,
        temperature: 0
      });

  const [attendanceStats, setAttendanceStats] = useState<any[]>([]);

  useEffect(() => {
    // Abonnement aux logs en temps réel
    const unsubscribeLogs = websocketService.subscribe('logs', (data) => {
      setRealtimeLogs(prevLogs => {
        const newLogs = [...prevLogs, data];
        // Garder seulement les 20 logs les plus récents
        return newLogs.slice(-20);
      });
    });

    // Abonnement au statut des modules - maintenant géré par useModulesRealtime
    // Pas besoin de s'abonner ici car le Dashboard utilise directement useModulesRealtime
    const unsubscribeModules = () => {}; // Placeholder pour éviter les erreurs

    // Abonnement aux alertes
    const unsubscribeAlerts = websocketService.subscribe('alerts', (data) => {
      setAlerts(data);
    });

    // Abonnement aux données de présence
    const unsubscribeAttendance = websocketService.subscribe('attendance_stats', (data) => {
      setAttendanceStats(data);
    });

    return () => {
      // Nettoyage des abonnements
      unsubscribeLogs();
      unsubscribeModules();
      unsubscribeAlerts();
      unsubscribeAttendance();
    };
  }, []);

  return {
    realtimeLogs,
    moduleStatus,
    alerts,
    attendanceStats
  };
};
