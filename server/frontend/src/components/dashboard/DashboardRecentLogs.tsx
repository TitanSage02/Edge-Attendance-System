import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock } from "lucide-react";
import { DashboardLogEntry } from "@/types/dashboard";
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

interface RecentLogsProps {
  logs: DashboardLogEntry[];
}

/**
 * Formater la date relative
 */
const formatDate = (date: Date): string => {
  if (date instanceof Date && !isNaN(date.getTime())) {
    return formatDistanceToNow(date, { addSuffix: true, locale: fr });
  }
  return 'Date inconnue';
};

/**
 * Composant affichant les logs récents sur le tableau de bord
 */
export const DashboardRecentLogs = ({ logs }: RecentLogsProps) => {
  return (
    <Card className="bg-white hover:shadow-md transition-all duration-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg text-[#1f3d7a]">Dernières actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {logs.length > 0 ? (
            logs.map((log) => (
              <div 
                key={log.id} 
                className="flex items-start space-x-4 p-2 rounded-md hover:bg-gray-50"
              >
                <div className="rounded-full bg-blue-100 p-2">
                  <Clock className="h-3.5 w-3.5 text-[#1f3d7a]" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">{log.action}</p>
                  <p className="text-xs text-gray-500">{log.details}</p>
                  <div className="flex items-center text-xs text-gray-500">
                    {log.userName && (
                      <span className="mr-3">{log.userName}</span>
                    )}
                    {log.moduleName && (
                      <span className="mr-3">{log.moduleName}</span>
                    )}
                    <span>{formatDate(new Date(log.timestamp))}</span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-4 text-gray-500">
              Aucune activité récente à afficher
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default DashboardRecentLogs;