import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import AddUserForm from "../components/admin/AddUserForm";
import UserRow from "../components/admin/UserRow";
import { useAuth } from "@/hooks/useAuth"; // Ajout de l'import useAuth
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Search,
  Plus,
  User as UserIcon,
} from "lucide-react";
import { useUsers } from "@/hooks/useUsers";
import { RolePermissions } from "@/types/permissionTypes";


const rolePermissions: RolePermissions = {
  admin: [
    { name: "Gestion des utilisateurs", description: "Créer, modifier et supprimer des utilisateurs" },
    { name: "Gestion des modules", description: "Gérer tous les modules de présence" },
    { name: "Accès aux logs", description: "Voir toutes les activités du système" },
    { name: "Paramètres système", description: "Modifier les paramètres système" },
  ],
  pedagogical: [
    { name: "Gestion des apprenants", description: "Gérer les fiches des apprenants" },
    { name: "Suivi des présences", description: "Consulter et modifier les présences" },
    { name: "Rapports", description: "Générer des rapports de présence" },
  ],
  technician: [
    { name: "Maintenance des modules", description: "Surveiller et entretenir les modules" },
    { name: "Alertes techniques", description: "Recevoir et gérer les alertes techniques" },
    { name: "Configuration matérielle", description: "Paramétrer les équipements" },
  ],
};

const AdminUtilisateurs = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [open, setOpen] = useState(false);
  const { hasRole } = useAuth(); // Ajout de la récupération de hasRole
    
  // Vérification du rôle directement dans le composant
  const userIsAdmin = hasRole("admin");
 //  console.log("User is admin:", userIsAdmin);
  
  // Use the useUsers hook
  const { users, isLoading } = useUsers();
  const filteredUsers = users?.filter((user) => {
    const searchStr = `${user.firstName} ${user.lastName} ${user.email}`.toLowerCase();
    return searchStr.includes(searchQuery.toLowerCase());
  }) || [];

  return (
    <MainLayout requiredRoles={["admin"]}>
      <div className="container mx-auto py-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
          <h1 className="text-xl font-bold">Gestion des utilisateurs</h1>
          <div className="space-x-2 flex items-center">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Rechercher des utilisateurs..."
                className="pl-8 h-9 text-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button size="sm" className="h-9 text-sm bg-[#1f3d7a] hover:bg-[#2a4f94]">
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  Ajouter
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                  <DialogTitle>Ajouter un utilisateur</DialogTitle>
                  <DialogDescription className="text-xs">
                    Créez un nouvel utilisateur pour accéder à la plateforme.
                  </DialogDescription>
                </DialogHeader>
                <AddUserForm 
                  onSuccess={() => setOpen(false)} 
                  onCancel={() => setOpen(false)} 
                />
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <div className="rounded-md border bg-white">
          <Table>            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-4">
                    Chargement...
                  </TableCell>
                </TableRow>
              ) : filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-4 text-sm text-gray-500">
                    Aucun utilisateur trouvé
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((user) => (
                  <UserRow key={user.id} user={user} />
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </MainLayout>  );
};

export default AdminUtilisateurs;
