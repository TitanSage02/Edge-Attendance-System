import { useState, useEffect } from 'react';
import { websocketService } from './index';
import { Module } from '@/types';
import { WebSocketModuleStatus } from '@/types/moduleTypes';

// Helper pour formater l'uptime en format lisible
const formatUptime = (uptimeSeconds: number): string => {
  if (!uptimeSeconds || uptimeSeconds <= 0) return "0s";
  
  const seconds = Math.floor(uptimeSeconds);
  const days = Math.floor(seconds / 86400); // 24 * 60 * 60
  const hours = Math.floor((seconds % 86400) / 3600); // 60 * 60
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  
  const parts: string[] = [];
  
  if (days > 0) parts.push(`${days}j`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}s`);
  
  // Limiter à 3 parties pour éviter des formats trop longs
  return parts.slice(0, 3).join(' ');
};

// Helper pour mapper WebSocketModuleStatus vers le type de vue Module
const mapToModuleView = (statusData: WebSocketModuleStatus, existingModule?: Module): Module => {
  const baseModule: Partial<Module> = existingModule || {
    uid: statusData.module_uid, // Garder comme number
    name: `Module ${statusData.module_uid}`,
    emplacement: "N/A",
    faceChecked: false,
    rfidChecked: false,
  };

  return {
    ...baseModule,
    uid: statusData.module_uid, // Garder comme number
    status: statusData.status as Module['status'], 
    last_seen: new Date(statusData.last_seen).toISOString(),
    uptime: statusData.uptime ? formatUptime(statusData.uptime) : (existingModule?.uptime || "0s"), 
    // version: statusData.version || undefined,
    // temperature: existingModule?.temperature || null,
    // methods: existingModule?.methods || { rfid: false, facial: false},
  } as Module;
};

/**
 * Hook pour les données en temps réel des modules
 */
export const useModulesRealtime = (initialModules: Module[] = []) => {
  const [modules, setModules] = useState<Module[]>([]);
  const [restartStatus, setRestartStatus] = useState<Record<string, string>>({});

  // Charger les modules depuis localStorage au démarrage et merger avec initialModules
  useEffect(() => {
    const savedModules = localStorage.getItem('crec_modules_realtime');
    let realtimeModules: Module[] = [];
    
    if (savedModules) {
      try {
        realtimeModules = JSON.parse(savedModules);
      } catch (error) {
        console.warn('Erreur lors du chargement des modules sauvegardés:', error);
      }
    }

    // Merger les modules initiaux avec les modules en temps réel sauvegardés
    const mergedModules = [...initialModules];
    
    realtimeModules.forEach(realtimeModule => {
      const existingIndex = mergedModules.findIndex(m => m.uid === realtimeModule.uid);
      if (existingIndex >= 0) {
        // Mettre à jour le module existant avec les données temps réel les plus récentes
        mergedModules[existingIndex] = {
          ...mergedModules[existingIndex],
          ...realtimeModule,
          // Conserver certaines propriétés des modules initiaux
          name: mergedModules[existingIndex].name || realtimeModule.name,
          emplacement: mergedModules[existingIndex].emplacement || realtimeModule.emplacement,
        };
      } else {
        // Ajouter le nouveau module découvert via WebSocket
        mergedModules.push(realtimeModule);
      }
    });

    setModules(mergedModules);
  }, [initialModules]);

  // Sauvegarder les modules dans localStorage quand ils changent
  useEffect(() => {
    if (modules.length > 0) {
      localStorage.setItem('crec_modules_realtime', JSON.stringify(modules));
    }
  }, [modules]);

  useEffect(() => {
    const handleModuleMessage = (message: any) => {
      if (!message || !message.type || !message.data) return;

      if (message.type === 'module_status') {
        const statusUpdate = message.data as WebSocketModuleStatus;
        
        setModules(prevModules => {
          const existingModuleIndex = prevModules.findIndex(module => module.uid === statusUpdate.module_uid);
          
          if (existingModuleIndex >= 0) {
            // Mettre à jour le module existant
            const updatedModules = [...prevModules];
            updatedModules[existingModuleIndex] = mapToModuleView(statusUpdate, prevModules[existingModuleIndex]);
            return updatedModules;
          } else {
            // Ajouter un nouveau module découvert
            const newModule = mapToModuleView(statusUpdate);
            console.log(`🆕 Nouveau module découvert: ${statusUpdate.module_uid}`);
            return [...prevModules, newModule];
          }
        });
      }
    };

    const unsubscribeModuleStatus = websocketService.subscribe('modules', handleModuleMessage);
    
    // Aussi s'abonner au type 'module_status' car les messages peuvent arriver via le channel 'all'
    const unsubscribeModuleStatusType = websocketService.subscribe('module_status', (data) => {
      console.log('📊 Message module_status reçu via type:', data);
      handleModuleMessage({ type: 'module_status', data });
    });

    const unsubscribeModuleRestart = websocketService.subscribe('module_restart', (data) => {
      const { moduleId, status } = data;
      setRestartStatus(prev => ({ ...prev, [moduleId]: status }));
      if (status === 'completed' || status === 'failed') {
        setTimeout(() => {
          setRestartStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[moduleId];
            return newStatus;
          });
        }, 5000);
      }
    });

    return () => {
      unsubscribeModuleStatus();
      unsubscribeModuleStatusType();
      unsubscribeModuleRestart();
    };
  }, []);

  return {
    modules,
    restartStatus,
    isRestarting: (moduleId: number) => restartStatus[moduleId.toString()] === 'pending',
    // Fonction pour nettoyer manuellement les modules obsolètes
    clearObsoleteModules: () => {
      const now = new Date();
      setModules(prevModules => 
        prevModules.filter(module => {
          if (!module.last_seen) return true; // Garder les modules sans last_seen
          const lastSeen = new Date(module.last_seen);
          const hoursSinceLastSeen = (now.getTime() - lastSeen.getTime()) / (1000 * 60 * 60);
          return hoursSinceLastSeen < 24; // Supprimer les modules non vus depuis plus de 24h
        })
      );
    },
    // Fonction pour effacer complètement le cache
    clearCache: () => {
      localStorage.removeItem('crec_modules_realtime');
      setModules(initialModules);
    }
  };
};
