
import { useState, useMemo } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import AddUserForm from "./AddUserForm";
import UserRow from "./UserRow";
import { useUsers } from "@/hooks/useUsers";

/**
 * Composant AdminUtilisateurs - Version utilisée comme sous-composant
 * Cette version est conçue pour être utilisée dans d'autres composants
 * sans le MainLayout (qui est déjà inclus dans la page principale)
 */
const AdminUtilisateurs = () => {
  const { users, isLoading, error, refetch } = useUsers();
  const [searchQuery, setSearchQuery] = useState("");
  const [open, setOpen] = useState(false);

  const filteredUsers = useMemo(() => {
    return (users || []).filter((user) => {
      const searchStr = `${user.firstName} ${user.lastName} ${user.email}`.toLowerCase();
      return searchStr.includes(searchQuery.toLowerCase());
    });
  }, [users, searchQuery]);
  if (isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-6 text-red-500">
        Erreur lors du chargement des utilisateurs
      </div>
    );
  }
  return (
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
              <Button size="sm" className="h-9 text-sm bg-[#1f3d7a] hover:bg-[#2a4f94]" aria-label="Ajouter un utilisateur">
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
                onSuccess={() => { setOpen(false); refetch(); }}
                onCancel={() => setOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredUsers.map((user) => (
              <UserRow key={user.id} user={user} />
            ))}
            {filteredUsers.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-4 text-sm text-gray-500">
                  Aucun utilisateur trouvé
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default AdminUtilisateurs;
