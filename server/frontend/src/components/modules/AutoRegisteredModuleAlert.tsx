import { AlertTriangle, Settings, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Module } from "@/types/moduleTypes";
import { ModuleAutoRegistrationService } from "@/services/moduleAutoRegistration";

interface AutoRegisteredModuleAlertProps {
  modules: Module[];
  onConfigureModule: (module: Module) => void;
}

/**
 * Composant d'alerte pour les modules auto-enregistrés nécessitant une configuration
 */
const AutoRegisteredModuleAlert: React.FC<AutoRegisteredModuleAlertProps> = ({
  modules,
  onConfigureModule,
}) => {
  const unconfiguredModules = ModuleAutoRegistrationService.needsConfiguration(modules);

  if (unconfiguredModules.length === 0) {
    return null;
  }

  return (
    <Card className="border-orange-200 bg-orange-50">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-orange-800">
          <AlertTriangle className="h-5 w-5" />
          Modules nécessitant une configuration
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-orange-700 mb-4">
          {unconfiguredModules.length} module(s) auto-enregistré(s) nécessitent une configuration complète :
        </p>
        
        <div className="space-y-3">
          {unconfiguredModules.map((module) => (
            <div
              key={module.uid}
              className="flex items-center justify-between p-3 bg-white rounded-lg border border-orange-200"
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4 text-orange-500" />
                  <span className="font-medium">UID {module.uid}</span>
                </div>
                
                <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                  Auto-enregistré
                </Badge>
                
                {module.status === 'online' && (
                  <Badge variant="default" className="bg-green-100 text-green-800">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    En ligne
                  </Badge>
                )}
              </div>
              
              <Button
                size="sm"
                onClick={() => onConfigureModule(module)}
                className="bg-orange-600 hover:bg-orange-700"
              >
                Configurer
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default AutoRegisteredModuleAlert;
