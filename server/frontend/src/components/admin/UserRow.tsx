import { TableCell, TableRow } from "@/components/ui/table";
import { Mail, User, MoreHorizontal, Edit, Copy, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { User as UserType, UserRole } from "@/types/userTypes";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { useUsers } from "@/hooks/useUsers";
import { useState } from "react";
import EditUserForm from "./EditUserForm";

interface Props { 
  user: UserType; 
}

// Helper function to convert role to French
function mapRoleToFrench(role: UserRole): string {
  const roleMap: Record<UserRole, string> = {
    admin: 'Administrateur',
    pedagogical: 'Responsable Pédagogique',
    technician: 'Technicien'
  };
  return roleMap[role] || role;
}

const UserRow = ({ user }: Props) => {
  const { success, error: showError } = useUnifiedToast();
  const { remove } = useUsers();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const handleDeleteConfirm = () => {
    remove.mutate(user.id, {
      onSuccess: () => {
        success("L'utilisateur a été supprimé avec succès et un email de notification lui a été envoyé.", { title: "Utilisateur supprimé" });
        setDeleteDialogOpen(false);
      },
      onError: (error) => {
        showError("Impossible de supprimer l'utilisateur. Veuillez réessayer.", { title: "Erreur" });
        setDeleteDialogOpen(false);
      },
    });
  };
  const handleEditSuccess = () => {
    setEditDialogOpen(false);
    success("Les informations de l'utilisateur ont été mises à jour avec succès.", { title: "Utilisateur modifié" });
  };

  const handleCopyEmail = () => {
    navigator.clipboard.writeText(user.email);
    success("L'adresse email a été copiée dans le presse-papiers.", { title: "Email copié" });
  };

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center space-x-2">
          <User className="w-4 h-4 text-gray-500" />
          <span className="text-sm">{user.firstName} {user.lastName}</span>
        </div>
      </TableCell>
      <TableCell>
        <a href={`mailto:${user.email}`} className="text-sm text-blue-500 hover:underline flex items-center">
          <Mail className="w-3.5 h-3.5 mr-1" />
          {user.email}
        </a>
      </TableCell>
      <TableCell className="text-sm">{mapRoleToFrench(user.role)}</TableCell>
      <TableCell className="text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0" aria-label="Ouvrir le menu">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>          
          <DropdownMenuContent align="end" className="bg-white">
            <DropdownMenuItem onClick={() => setEditDialogOpen(true)}>
              <Edit className="h-4 w-4 mr-2" /> Modifier
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleCopyEmail}>
              <Copy className="h-4 w-4 mr-2" /> Copier l'email
            </DropdownMenuItem>
            
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
              <AlertDialogTrigger asChild>
                <DropdownMenuItem 
                  className="text-red-600 focus:text-red-600"
                  onSelect={(e) => {
                    e.preventDefault();
                    setDeleteDialogOpen(true);
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" /> Supprimer
                </DropdownMenuItem>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Êtes-vous vraiment sûr ?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Cette action ne peut pas être annulée. Cela supprimera définitivement le compte de{" "}
                    <strong>{user.firstName} {user.lastName}</strong> ({user.email}) et toutes ses données associées.
                    <br /><br />
                    Un email de notification sera automatiquement envoyé à l'utilisateur pour l'informer de la suppression de son compte.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Annuler</AlertDialogCancel>
                  <AlertDialogAction 
                    onClick={handleDeleteConfirm}
                    className="bg-red-500 hover:bg-red-600 focus:ring-red-500"
                  >
                    Oui, supprimer définitivement
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>

      {/* Boîte de dialogue d'édition d'utilisateur */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Modifier l'utilisateur</DialogTitle>
            <DialogDescription>
              Vous pouvez modifier les informations de l'utilisateur {user.firstName} {user.lastName}.
              Note: l'adresse email n'est pas modifiable.
            </DialogDescription>
          </DialogHeader>
          <EditUserForm 
            user={user} 
            onSuccess={handleEditSuccess} 
            onCancel={() => setEditDialogOpen(false)} 
          />
        </DialogContent>
      </Dialog>
    </TableRow>
  );
};

export default UserRow;