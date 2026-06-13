import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useIsMobile } from "@/hooks/use-mobile";

import MainLayout from "@/components/layout/MainLayout";

import DashboardAttendanceChart from "@/components/dashboard/DashboardAttendanceChart";
import DashboardModuleStatus from "@/components/dashboard/DashboardModuleStatus";
import DashboardRecentLogs from "@/components/dashboard/DashboardRecentLogs";
import DashboardAlerts from "@/components/dashboard/DashboardAlerts";

import { DashboardMetrics } from "@/types/dashboard";
import { dashboardApi } from "@/services/api/dashboard";
import { modulesApi } from "@/services/api/modules";
import { useModulesRealtime } from "@/services/websocket/useModulesRealtime";
import { Module } from "@/types";

/**
 * Hook pour récupérer les metrics du dashboard
 **/
function useDashboardMetrics() {
  return useQuery<DashboardMetrics>({
    queryKey: ["dashboardMetrics"],
    queryFn: () => dashboardApi.getMetrics(),
    retry: 1,
    staleTime: 15_000,
    gcTime: 15_000,
    refetchInterval: 15_000,
  });
}

/**
 * Hook pour récupérer la liste des modules
 **/
function useModules() {
  return useQuery<Module[]>({
    queryKey: ["modules"],
    queryFn: () => modulesApi.getModules(),
    retry: 1,
    staleTime: 30_000,
    gcTime: 30_000,
  });
}

/**
 * Fonction utilitaire pour calculer les stats des modules
 **/
function calculateModuleStats(modules: Module[]) {
  const stats = {
    total: modules.length,
    online: 0,
    offline: 0,
    standby: 0,
  };

  modules.forEach(module => {
    switch (module.status) {
      case 'online':
        stats.online++;
        break;
      case 'offline':
        stats.offline++;
        break;
      case 'idle':
        stats.standby++;
        break;
      default:
        stats.offline++;
    }
  });

  return stats;
}

const Dashboard = () => {
  const { data: metrics, isLoading } = useDashboardMetrics();
  const { data: initialModules = [] } = useModules();
  const { modules: realtimeModules } = useModulesRealtime(initialModules);
  const isMobile = useIsMobile();

  // Initialisation à des zéros / tableaux vides
  const [localMetrics, setLocalMetrics] = useState<DashboardMetrics>({
    todayAttendance: { 
      total: 0, 
      byClass: [],
    },
    alerts: { 
      total: 0, 
    },
    modules: {
      total: 0,
      online: 0,
      offline: 0,
      standby: 0,
    },
    recentLogs: [],
  });

  // Quand les metrics arrivent, on met à jour localMetrics (sauf pour les modules)
  useEffect(() => {
    if (metrics) {
      setLocalMetrics(prev => ({
        ...metrics,
        modules: prev.modules, // Garder les stats des modules en temps réel
      }));
    }
  }, [metrics]);

  // Calculer les stats des modules en temps réel
  useEffect(() => {
    const moduleStats = calculateModuleStats(realtimeModules);
    setLocalMetrics(prev => ({
      ...prev,
      modules: moduleStats,
    }));
  }, [realtimeModules]);

  return (
    <MainLayout>
      <div className="space-y-3 sm:space-y-6 px-2 sm:px-4 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-4 pb-2 sm:pb-4">
          <h1 className="text-lg sm:text-xl font-bold tracking-tight text-[#1f3d7a]">Tableau de bord</h1>
          <p className="text-xs sm:text-sm text-gray-500 whitespace-nowrap">
            {new Date().toLocaleDateString("fr-FR", {
              weekday: isMobile ? undefined : "long",
              year: "numeric",
              month: isMobile ? "short" : "long",
              day: "numeric",
            })}
          </p>
        </div>

        {/* Si on charge toujours, on peut afficher un loader */}
        {isLoading && (
          <div className="flex items-center justify-center py-6 sm:py-8">
            <div className="animate-spin rounded-full h-8 w-8 sm:h-12 sm:w-12 border-t-2 border-b-2 border-[#1f3d7a]"></div>
          </div>
        )}

        {/* Grille principale */}
        {(() => {
          const cleanByClass = localMetrics.todayAttendance.byClass
            .filter(c => typeof c.name === 'string' && typeof c.present === 'number' && typeof c.absent === 'number')
            .map(c => ({
              name: c.name,
              present: Math.max(0, c.present),
              absent: Math.max(0, c.absent)
            }));

          return (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-5">
              <div className="bg-white rounded-lg shadow-sm p-3 sm:p-4 min-h-[300px] flex flex-col">
                <DashboardAttendanceChart
                  data={cleanByClass}
                />
              </div>

              <div className="space-y-3 sm:space-y-5">
                <div className="bg-white rounded-lg shadow-sm p-3 sm:p-4">
                  <DashboardModuleStatus status={localMetrics.modules} />
                </div>

                <div className="bg-white rounded-lg shadow-sm p-3 sm:p-4">
                  <DashboardAlerts
                    total={localMetrics.alerts.total}
                  />
                </div> 
              </div>
            </div>
          );
        })()}

        {/* Logs récents */}
        <div className="bg-white rounded-lg shadow-sm p-3 sm:p-4 overflow-x-auto">
          <DashboardRecentLogs 
            logs={localMetrics.recentLogs.map(log => ({
              ...log,
              timestamp: log.timestamp ? new Date(log.timestamp).toISOString() : "Invalide"
            }))} 
          />
        </div>
      </div>
    </MainLayout>
  );
};

export default Dashboard;