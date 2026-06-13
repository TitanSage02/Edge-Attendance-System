import { useState, useEffect } from 'react';
import { websocketService } from './index';
import { Attendance } from '@/types';
import { toastManager } from "@/services/toastManager";

export interface PresenceUpdate {
  type: 'new_presence' | 'presence_update';
  presence_id: number;
  student_id: string;
  module_uid: number;
  status: boolean;
  timestamp: string;
}

/**
 * Hook pour les données de présence en temps réel
 */
export const usePresenceRealtime = (date?: string) => {
  const [attendanceRecords, setAttendanceRecords] = useState<Attendance[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [recentPresences, setRecentPresences] = useState<PresenceUpdate[]>([]);
  const [lastUpdate, setLastUpdate] = useState<PresenceUpdate | null>(null);
  const [stats, setStats] = useState({
    present: 0,
    absent: 0,
    late: 0,
    total: 0,
    byClass: [] as { name: string; present: number; absent: number; late: number }[]
  });

  useEffect(() => {
    // Si une date est spécifiée, demander les données pour cette date
    if (date) {
      websocketService.send('request_attendance', { date });
    }

    // S'abonner aux mises à jour de présence existantes
    const unsubscribeAttendance = websocketService.subscribe('attendance', (data) => {
      if (data.records) {
        setAttendanceRecords(data.records);
      }
      if (data.stats) {
        setStats(data.stats);
      }
      setLoading(false);
    });

    // Nouveau : S'abonner aux présences MQTT en temps réel
    const handlePresenceMessage = (message: any) => {
      if (!message || !message.type) return;

      if (message.type === 'new_presence' || message.type === 'presence_update') {
        const presenceUpdate: PresenceUpdate = {
          type: message.type,
          presence_id: message.presence_id,
          student_id: message.student_id,
          module_uid: message.module_uid,
          status: message.status,
          timestamp: message.timestamp,
        };

        setLastUpdate(presenceUpdate);
        
        // Ajouter à la liste des présences récentes (limite à 20)
        setRecentPresences(prev => {
          const updated = [presenceUpdate, ...prev];
          return updated.slice(0, 20);
        });

        // Afficher une notification
        toastManager.success(
          `Présence détectée : Étudiant ${presenceUpdate.student_id}`,
          { duration: 3000 }
        );
      }
    };

    // S'abonner au canal presence pour les nouveaux events MQTT
    const unsubscribePresence = websocketService.subscribe('presence', handlePresenceMessage);
    
    // S'abonner aussi au canal all pour les mises à jour générales
    const unsubscribeAll = websocketService.subscribe('all', (message: any) => {
      if (message.type === 'presence_update' && message.data) {
        handlePresenceMessage(message.data);
      }
    });

    // S'abonner aux événements de pointage existants
    const unsubscribeEvent = websocketService.subscribe('attendance_event', (data) => {
      // Nouvelle entrée ou sortie détectée
      const { student, action, moduleId, moduleLocation } = data;
        toastManager.info(
        `${student.firstName} ${student.lastName} ${action === 'in' ? 'entré' : 'sorti'} - ${moduleLocation}`,
        { duration: 3000 }
      );
      
      // Mettre à jour les données locales
      if (action === 'in') {
        setAttendanceRecords(prev => [
          {
            id: data.id,
            student_id: student.id,
            module_uid: moduleId,
            status: true,
            timestamp: new Date().toISOString(),
            entry_time: new Date().toISOString(),
            student: {
              id: student.id,
              firstName: student.firstName,
              lastName: student.lastName,
              classGroup: student.classGroup
            }
          },
          ...prev
        ]);
      } else if (action === 'out') {
        setAttendanceRecords(prev => 
          prev.map(record => {
            if (record.student_id === student.id && !record.exit_time) {
              return {
                ...record,
                exit_time: new Date().toISOString()
              };
            }
            return record;
          })
        );
      }
    });

    return () => {
      unsubscribeAttendance();
      unsubscribeEvent();
      unsubscribePresence();
      unsubscribeAll();
    };
  }, [date]);

  return {
    attendanceRecords,
    stats,
    loading,
    recentPresences,
    lastUpdate,
    hasNewPresences: recentPresences.length > 0,
    refreshAttendance: (selectedDate?: string) => {
      setLoading(true);
      websocketService.send('request_attendance', { date: selectedDate || date });
    }
  };
};
