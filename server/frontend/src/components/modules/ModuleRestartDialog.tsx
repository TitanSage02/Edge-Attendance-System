
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface ModuleRestartDialogProps {
  isOpen: boolean;
  onClose: () => void;
  moduleName: string;
  moduleId: string;
  onConfirm: () => Promise<void>;
  status?: string;
}

/**
 * Dialogue de confirmation et suivi pour le redémarrage d'un module
 */
export const ModuleRestartDialog = ({
  isOpen,
  onClose,
  moduleName,
  moduleId,
  onConfirm,
  status = "idle"
}: ModuleRestartDialogProps) => {
  const [progress, setProgress] = useState(0);
  const [internalStatus, setInternalStatus] = useState(status);
  
  // État du redémarrage
  const isIdle = internalStatus === "idle";
  const isRestarting = internalStatus === "restarting";
  const isSuccess = internalStatus === "success";
  const isError = internalStatus === "error";
  
  // Mettre à jour le statut interne si le statut externe change
  useEffect(() => {
    setInternalStatus(status);
  }, [status]);
  
  // Simuler la progression pendant le redémarrage
  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (isRestarting) {
      setProgress(0);
      
      timer = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + 2;
          
          // Atteindre 90% maximum en mode simulation
          // Le backend confirmera quand on atteint 100%
          return Math.min(newProgress, 90);
        });
      }, 500);
    }
    
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isRestarting]);
  
  // Déclencher le redémarrage du module
  const handleRestart = async () => {
    setInternalStatus("restarting");
    try {
      await onConfirm();
      // Note: Le succès ou l'échec sera normalement notifié par WebSocket
      // Ici on simule le succès après quelques secondes
      setTimeout(() => {
        setProgress(100);
        setInternalStatus("success");
      }, 8000);
    } catch (error) {
      setInternalStatus("error");
    }
  };
  
  // Fermer la boîte de dialogue
  const handleClose = () => {
    if (!isRestarting) {
      setInternalStatus("idle");
      setProgress(0);
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {isIdle && `Redémarrer le module ${moduleName}`}
            {isRestarting && `Redémarrage en cours...`}
            {isSuccess && `Redémarrage réussi`}
            {isError && `Erreur de redémarrage`}
          </DialogTitle>
          <DialogDescription>
            {isIdle && "Cette action va redémarrer le module. Le module sera indisponible un moment."}
            {isRestarting && "Veuillez patienter pendant le redémarrage du module."}
            {isSuccess && "Le module a été redémarré avec succès."}
            {isError && "Une erreur est survenue lors du redémarrage du module. Veuillez réessayer."}
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          {isRestarting && (
            <div className="space-y-4">
              <Progress value={progress} className="h-2 w-full" />
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                <p className="text-sm text-gray-500">
                  {progress < 25 && "Envoi de la commande de redémarrage..."}
                  {progress >= 25 && progress < 60 && "Arrêt des services en cours..."}
                  {progress >= 60 && "Rémarrage des services..."}
                </p>
              </div>
            </div>
          )}
          
          {isSuccess && (
            <div className="flex flex-col items-center justify-center gap-3 py-4">
              <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <p className="text-sm text-gray-600">
                Le module {moduleName} est à nouveau opérationnel.
              </p>
            </div>
          )}
          
          {isError && (
            <div className="flex flex-col items-center justify-center gap-3 py-4">
              <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
              <p className="text-sm text-gray-600">
                Une erreur de communication s'est produite. Veuillez vérifier la connexion réseau du module.
              </p>
            </div>
          )}
        </div>
        
        <div className="flex justify-end gap-2">
          {isIdle && (
            <>
              <Button variant="outline" onClick={handleClose}>Annuler</Button>
              <Button onClick={handleRestart}>Redémarrer</Button>
            </>
          )}
          
          {isRestarting && (
            <Button disabled>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              En cours...
            </Button>
          )}
          
          {(isSuccess || isError) && (
            <Button onClick={handleClose}>Fermer</Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ModuleRestartDialog;
