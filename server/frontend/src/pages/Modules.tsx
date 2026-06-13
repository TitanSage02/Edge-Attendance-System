import { useState, useEffect, useMemo } from "react";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";

import MainLayout from "../components/layout/MainLayout";

import { modulesApi } from "@/services/api/modules";
import { Module } from "@/types/moduleTypes";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PlusCircle, Layout, List, Loader2 } from "lucide-react";
import ModuleForm from "@/components/modules/ModuleForm";
import ModulesList from "@/components/modules/ModulesList";
import ModuleRestartDialog from "@/components/modules/ModuleRestartDialog";
import AutoRegisteredModuleAlert from "@/components/modules/AutoRegisteredModuleAlert";
import { useModulesRealtime } from "@/services/websocket/useModulesRealtime";
import { ModuleAutoRegistrationService } from "@/services/moduleAutoRegistration";

const Modules = () => {
  const { success, error: showError } = useUnifiedToast();
  const [modules, setModules] = useState<Module[]>([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [currentModule, setCurrentModule] = useState<Module | undefined>(undefined);
  const [view, setView] = useState<"grid" | "list">("grid");
  
  // État pour le dialogue de redémarrage
  const [restartDialog, setRestartDialog] = useState<{
    isOpen: boolean;
    moduleId: string;
    moduleName: string;
  }>({
    isOpen: false,
    moduleId: "",
    moduleName: "",
  });  // Hook pour les mises à jour en temps réel
  const { modules: realtimeModules, isRestarting } = useModulesRealtime(modules);
  
  useEffect(() => {
    const fetchModules = async () => {
      try {
        const data = await modulesApi.getModules();
       //  console.log("Modules chargés depuis l'API:", data);
        setModules(data);
      } catch (error) {
        console.error("Erreur lors du chargement des modules:", error);
        showError("Impossible de charger les modules depuis le serveur", { title: "Erreur de chargement" });
      }
    };
    
    fetchModules();
  }, [showError]);

  // Utiliser tous les modules : prioriser les modules en temps réel pour les mises à jour de statut,
  // mais s'assurer que tous les modules de l'API sont affichés
  const displayModules = useMemo(() => {
    if (realtimeModules.length === 0) {
      return modules;
    }
    
    // Fusionner les modules : garder tous les modules de l'API mais mettre à jour avec les données temps réel
    const realtimeMap = new Map(realtimeModules.map(m => [m.uid, m]));
    
    return modules.map(module => {
      const realtimeModule = realtimeMap.get(module.uid);
      return realtimeModule || module;
    });
  }, [modules, realtimeModules]);

  const handleAddModule = async (moduleData: Partial<Module>) => {
    try {
      const newModule = await modulesApi.createModule(moduleData);
      setModules((prev) => [...prev, newModule]);
      success(`Le module ${newModule.name} a été ajouté.`, { title: "Module ajouté" });
      setIsAddDialogOpen(false);
    } catch (error) {
      showError("Échec de l'ajout du module.", { title: "Erreur" });
    }
  };

  const handleEditModule = async (moduleData: Partial<Module>) => {
    if (!currentModule) return;
    try {
      const updated = await modulesApi.updateModule(currentModule.uid, moduleData);
      setModules((prev) =>
        prev.map((m) => (m.uid === updated.uid ? updated : m))
      );
      success(`Le module ${updated.name} a été mis à jour.`, { title: "Module mis à jour" });
      setCurrentModule(undefined);
    } catch (error) {
      showError("Échec de la mise à jour du module.", { title: "Erreur" });
    }
  };

  const handleDeleteModule = async (uid: number) => {
    try {
      await modulesApi.deleteModule(uid);
      setModules((prev) => prev.filter((m) => m.uid !== uid));
      success("Le module a été supprimé avec succès.", { title: "Module supprimé" });
    } catch (error) {
      showError("Échec de la suppression du module.", { title: "Erreur" });
    }
  };
  const handleRebootModule = async (uid: number) => {
    const module = displayModules.find(m => m.uid === uid);
    if (!module) return;
    
    // Ouvrir le dialogue de redémarrage
    setRestartDialog({
      isOpen: true,
      moduleId: uid.toString(), // Convertir en string pour l'affichage
      moduleName: module.name,
    });
  };

  const handleConfirmRestart = async () => {
    try {
      const moduleId = parseInt(restartDialog.moduleId);
      await modulesApi.restartModule(moduleId);
      success("Commande de redémarrage envoyée avec succès", { title: "Redémarrage en cours" });
    } catch (error) {
      showError("Échec de la requête de redémarrage.", { title: "Erreur" });
      throw error; // Relancer l'erreur pour que le dialogue puisse la gérer
    }
  };

  const handleCloseRestartDialog = () => {
    setRestartDialog({
      isOpen: false,
      moduleId: "",
      moduleName: "",
    });
  };

  const refreshModules = async () => {
    try {
      const data = await modulesApi.getModules();
      setModules(data);
      success("Les données ont été mises à jour.", { title: "Actualisation réussie" });
    } catch (error) {
      showError("Impossible d'actualiser les données.", { title: "Erreur" });
    }
  };
  return (
    <MainLayout requiredRoles={["admin", "technician"]}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Gestion des Modules</h1>
            <p className="text-muted-foreground">
              Ajoutez, modifiez et surveillez les modules de contrôle d'accès
            </p>
          </div>
          
          <div className="flex gap-2">
            <Tabs value={view} onValueChange={(v) => setView(v as "grid" | "list")} className="hidden sm:flex">
              <TabsList>
                <TabsTrigger value="grid">
                  <Layout className="h-4 w-4 mr-2" />
                  Grille
                </TabsTrigger>
                <TabsTrigger value="list">
                  <List className="h-4 w-4 mr-2" />
                  Liste
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Ajouter un module
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[550px]">
                <DialogHeader>
                  <DialogTitle>Ajouter un nouveau module</DialogTitle>
                  <DialogDescription>
                    Configurez les détails du nouveau module de contrôle d'accès.
                  </DialogDescription>
                </DialogHeader>
                <ModuleForm
                  onSubmit={handleAddModule}
                  onCancel={() => setIsAddDialogOpen(false)}
                />
              </DialogContent>
            </Dialog>
          </div>
        </div>
          {/* Statistics cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-white">
            <CardHeader className="pb-3 ">
              <CardTitle className="text-base">Total des modules</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{displayModules.length}</div>
              <p className="text-sm text-muted-foreground mt-1">
                Modules de contrôle d'accès
              </p>
            </CardContent>
          </Card>
          
          <Card className="bg-white">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Modules en ligne</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {displayModules.filter(m => m.status === "online").length}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {Math.round(
                  (displayModules.filter(m => m.status === "online").length / displayModules.length) * 100
                ) || 0}% du total
              </p>
            </CardContent>
          </Card>
          
          <Card className="bg-white">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Modules hors ligne</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">
                {displayModules.filter(m => m.status === "offline").length}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {Math.round(
                  (displayModules.filter(m => m.status === "offline").length / displayModules.length) * 100
                ) || 0}% du total
              </p>
            </CardContent>
          </Card>
        </div>
          {/* Modules list or grid view */}
        {view === "list" ? (
          <ModulesList
            modules={displayModules}
            onEdit={(module) => setCurrentModule(module)}
            onDelete={handleDeleteModule}
            onReboot={handleRebootModule}
            onRefreshData={refreshModules}
            isRestarting={isRestarting}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayModules.map((module) => {
              const moduleIsRestarting = isRestarting(module.uid);
              
              return (
                <Card key={module.uid} className="overflow-hidden hover:shadow-md transition-shadow bg-white">
                  <CardHeader className="pb-2 flex-row justify-between items-start space-y-0">
                    <div>
                      <CardTitle className="text-lg">{module.name}</CardTitle>
                      <CardDescription className="mt-1">
                        ID: {module.uid}
                      </CardDescription>
                    </div>
                    {module.status === "online" && (
                      <div className="status-dot online" />
                    )}
                    {module.status === "offline" && (
                      <div className="status-dot offline" />
                    )}
                    {module.status === "warning" && (
                      <div className="status-dot warning" />
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col space-y-2">
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                        <div className="text-muted-foreground">Emplacement:</div>
                        <div>{module.emplacement || "Non spécifié"}</div>
                        
                        <div className="text-muted-foreground">Méthodes:</div>
                        <div className="flex space-x-1">
                          {module.rfidChecked && (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                              RFID
                            </Badge>
                          )}
                          {module.faceChecked && (
                            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                              Facial
                            </Badge>
                          )}
                        </div>
                        
                        <div className="text-muted-foreground">Statut:</div>
                        <div>
                          {moduleIsRestarting ? (
                            <span className="text-blue-600 flex items-center">
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              Redémarrage...
                            </span>
                          ) : (
                            <>
                              {module.status === "online" && (
                                <span className="text-green-600">En ligne</span>
                              )}
                              {module.status === "offline" && (
                                <span className="text-red-600">Hors ligne</span>
                              )}
                              {module.status === "warning" && (
                                <span className="text-yellow-600">Avertissement</span>
                              )}
                            </>
                          )}
                        </div>
                        
                        <div className="text-muted-foreground">Uptime:</div>
                        <div>{module.uptime || "Non disponible"}</div>
                      </div>
                      
                      <div className="flex justify-end space-x-2 pt-4">
                        {moduleIsRestarting ? (
                          <Button 
                            variant="outline" 
                            size="sm"
                            disabled
                            className="cursor-not-allowed opacity-50"
                          >
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Redémarrage...
                          </Button>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleRebootModule(module.uid)}
                          >
                            Redémarrer
                          </Button>
                        )}
                        
                        <Button 
                          size="sm" 
                          onClick={() => setCurrentModule(module)}
                          disabled={moduleIsRestarting}
                        >
                          Modifier
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            
            {displayModules.length === 0 && (
              <div className="col-span-full flex items-center justify-center rounded-lg border border-dashed p-8">
                <div className="flex flex-col items-center text-center">
                  <h3 className="mt-4 text-lg font-semibold">Aucun module trouvé</h3>
                  <p className="mt-2 text-sm text-muted-foreground max-w-xs">
                    Vous n'avez pas encore ajouté de modules. Cliquez sur le bouton "Ajouter un module" pour commencer.
                  </p>
                  <Button 
                    onClick={() => setIsAddDialogOpen(true)}
                    className="mt-4"
                  >
                    <PlusCircle className="h-4 w-4 mr-2" />
                    Ajouter un module
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
        {/* Edit module dialog */}
      {currentModule && (
        <Dialog open={!!currentModule} onOpenChange={(open) => !open && setCurrentModule(undefined)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Modifier un module</DialogTitle>
              <DialogDescription>
                Modifiez les détails du module de contrôle d'accès.
              </DialogDescription>
            </DialogHeader>
            <ModuleForm
              module={currentModule}
              onSubmit={handleEditModule}
              onCancel={() => setCurrentModule(undefined)}
            />
          </DialogContent>
        </Dialog>
      )}

      {/* Restart module dialog */}
      <ModuleRestartDialog
        isOpen={restartDialog.isOpen}
        onClose={handleCloseRestartDialog}
        moduleName={restartDialog.moduleName}
        moduleId={restartDialog.moduleId}
        onConfirm={handleConfirmRestart}
      />
    </MainLayout>
  );
};

export default Modules;
