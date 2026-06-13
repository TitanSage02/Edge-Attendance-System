import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Server, Moon, ServerCrash, Thermometer } from "lucide-react";
import { Link } from "react-router-dom";

interface ModuleStatusProps {
  status: {
    online: number;
    offline: number;
    standby: number;
    temperature?: number;
  };
}

/**
 * Composant affichant l'état des modules sur le tableau de bord
 */
export const DashboardModuleStatus = ({ status }: ModuleStatusProps) => {
  return (
    <Link to="/modules">
      <Card className="bg-white hover:shadow-md transition-all duration-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-[#1f3d7a]">Statut des modules</CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-green-500" />
                <span>En ligne</span>
              </div>
              <span>{status.online || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Moon className="h-4 w-4 text-amber-500" />
                <span>En veille</span>
              </div>
              <span>{status.standby || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <ServerCrash className="h-4 w-4 text-red-500" />
                <span>Éteint</span>
              </div>
              <span>{status.offline || 0}</span>
            </div>
          
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

export default DashboardModuleStatus;
