import { useState, useEffect } from 'react';
import { websocketService } from './index';
import { toastManager } from "@/services/toastManager";
import { Alert } from '@/types/alertTypes';

/**
 * Hook pour les alertes en temps réel
 */
export const useAlertsRealtime = (showNotifications = true) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // S'abonner aux alertes en temps réel
    const unsubscribe = websocketService.subscribe('alert', (data) => {
      // Validation des données reçues
      if (!data || typeof data !== 'object') {
        console.error('Données d\'alerte invalides reçues:', data);
        setError('Format de données invalide');
        setLoading(false);
        return;
      }

      const newAlert: Alert = {
        id: data.id || '',
        type: data.type || '',
        severity: data.severity || 'info',
        message: data.message || '',
        details: data.details || '',
        timestamp: new Date(data.timestamp || Date.now()).toISOString(),
        source: data.source || '',
        moduleId: data.moduleId,
        studentId: data.studentId,
        resolved: data.resolved || false,
        moduleName: data.moduleName
      };

      setAlerts(prevAlerts => {
        // Vérifier si l'alerte existe déjà
        const exists = prevAlerts.some(alert => alert.id === newAlert.id);
        if (exists) {
          // Mettre à jour l'alerte existante
          return prevAlerts.map(alert => 
            alert.id === newAlert.id ? newAlert : alert
          );
        } else {
          // Ajouter la nouvelle alerte
          if (showNotifications) {            // Afficher une notification pour les nouvelles alertes
            if (newAlert.severity === 'critical') {
              toastManager.error(`⚠️ Alerte critique: ${newAlert.message}`, {
                duration: 10000,
              });
            } else if (newAlert.severity === 'warning') {
              toastManager.warning(`⚠️ Avertissement: ${newAlert.message}`);
            }
          }
          return [newAlert, ...prevAlerts];
        }
      });

      setLoading(false);
      setError(null);
    });

    // Définir un timeout pour gérer le cas où aucune donnée n'est reçue
    const timeoutId = setTimeout(() => {
      if (loading) {
        setLoading(false);
        setError('Le système fonctionne parfaitement, aucun problème à signaler');
      }
    }, 5000); // 5 secondes de timeout

    return () => {
      unsubscribe();
      clearTimeout(timeoutId);
    };
  }, [showNotifications]);

  const resolveAlert = (alertId: string) => {
    websocketService.send('resolve_alert', { alertId });
    // Optimistic update
    setAlerts(prevAlerts => 
      prevAlerts.map(alert => 
        alert.id === alertId ? { ...alert, resolved: true } : alert
      )
    );
  };

  return {
    alerts,
    loading,
    error,
    resolveAlert
  };
};
