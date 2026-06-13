import { useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Module } from "@/types";
import { MoreVertical, RefreshCw, Edit, Trash, Server, Loader2 } from "lucide-react";

interface ModulesListProps {
  modules: Module[];
  onEdit: (module: Module) => void;
  onDelete: (id: number) => void; // Changé de string à number
  onReboot: (id: number) => void; // Changé de string à number
  onRefreshData: () => void;
  isRestarting?: (moduleId: number) => boolean; // Changé de string à number
}

const ModulesList = ({ modules, onEdit, onDelete, onReboot, onRefreshData, isRestarting = () => false }: ModulesListProps) => {
  return (
    <div className="rounded-lg border shadow overflow-hidden">
      <div className="bg-white p-4 border-b flex justify-between items-center">
        <h3 className="font-medium">Liste des modules</h3>
        <Button variant="outline" size="sm" onClick={onRefreshData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Rafraîchir
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">ID</TableHead>
            <TableHead>Nom</TableHead>
            <TableHead>Emplacement</TableHead>
            <TableHead>Méthodes</TableHead>
            <TableHead>Statut</TableHead>
            <TableHead>Dernière activité</TableHead>
            <TableHead>Temps de fonctionnement</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {modules.map((module) => {
            const moduleIsRestarting = isRestarting(module.uid);
            
            return (
              <TableRow key={module.uid} className="hover:bg-gray-50">
                <TableCell className="font-medium">{module.uid}</TableCell>
                <TableCell>{module.name}</TableCell>
                <TableCell>{module.emplacement}</TableCell>
                <TableCell>
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
                </TableCell>
                <TableCell>
                  {moduleIsRestarting ? (
                    <div className="flex items-center">
                      <Loader2 className="h-3 w-3 mr-2 animate-spin text-blue-500" />
                      <span className="text-blue-600">Redémarrage...</span>
                    </div>
                  ) : (
                    <>
                      {module.status === "online" && (
                        <div className="flex items-center">
                          <div className="status-dot online mr-2" />
                          <span className="text-green-600">En ligne</span>
                        </div>
                      )}
                      {module.status === "offline" && (
                        <div className="flex items-center">
                          <div className="status-dot offline mr-2" />
                          <span className="text-red-600">Hors ligne</span>
                        </div>
                      )}
                      {module.status === "warning" && (
                        <div className="flex items-center">
                          <div className="status-dot warning mr-2" />
                          <span className="text-yellow-600">Avertissement</span>
                        </div>
                      )}
                    </>
                  )}
                </TableCell>
                <TableCell>
                  {module.last_seen ? (
                    format(new Date(module.last_seen), "dd/MM/yyyy HH:mm", { locale: fr })
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell>
                  {module.uptime || "—"}
                </TableCell>
                <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" disabled={moduleIsRestarting}>
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => onEdit(module)} disabled={moduleIsRestarting}>
                      <Edit className="h-4 w-4 mr-2" />
                      Modifier
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onReboot(module.uid)} disabled={moduleIsRestarting}>
                      {moduleIsRestarting ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin text-blue-500" />
                          <span className="text-blue-500">Redémarrage...</span>
                        </>
                      ) : (
                        <>
                          <Server className="h-4 w-4 mr-2 text-yellow-500" />
                          <span className="text-yellow-500">Redémarrer</span>
                        </>
                      )}
                    </DropdownMenuItem>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                          <Trash className="h-4 w-4 mr-2 text-red-500" />
                          <span className="text-red-500">Supprimer</span>
                        </DropdownMenuItem>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Êtes-vous sûr ?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Cette action ne peut pas être annulée. Le module sera définitivement supprimé
                            de votre système.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Annuler</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => onDelete(module.uid)}
                            className="bg-red-500 hover:bg-red-600"
                          >
                            Supprimer
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </DropdownMenuContent>
                </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
          {modules.length === 0 && (
            <TableRow>
              <TableCell colSpan={8} className="text-center py-6 text-gray-500">
                Aucun module trouvé
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default ModulesList;
