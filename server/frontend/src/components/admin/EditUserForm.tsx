import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { useUsers } from "@/hooks/useUsers";
import RolePermissionsDisplay from "./RolePermissionsDisplay";
import { User, UserRole } from "@/types/userTypes";
import { DialogFooter } from "@/components/ui/dialog";

interface Props {
  user: User;
  onSuccess: () => void;
  onCancel: () => void;
}

const EditUserForm = ({ user, onSuccess, onCancel }: Props) => {
  const [firstName, setFirstName] = useState(user.firstName);
  const [lastName, setLastName] = useState(user.lastName);
  const [role, setRole] = useState<UserRole>(user.role);  const [showPermissions, setShowPermissions] = useState(false);
  const { success, error } = useUnifiedToast();
  const { update } = useUsers();  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Inclure l'email actuel pour satisfaire la validation du backend
      await update.mutateAsync({ 
        id: user.id, 
        data: { 
          firstName, 
          lastName, 
          role,
          email: user.email, // Inclure l'email actuel sans le modifier
        } 
      });
      success("Utilisateur modifié avec succès.", { title: "Succès" });
      onSuccess();
    } catch (updateError) {
      error(updateError instanceof Error ? updateError.message : "Erreur lors de la modification", { title: "Erreur" });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="firstName" className="text-xs">Prénom</Label>
          <Input id="firstName" value={firstName} onChange={e => setFirstName(e.target.value)} className="h-8 text-sm" required />
        </div>
        <div>
          <Label htmlFor="lastName" className="text-xs">Nom</Label>
          <Input id="lastName" value={lastName} onChange={e => setLastName(e.target.value)} className="h-8 text-sm" required />
        </div>
      </div>
      <div>
        <Label htmlFor="email" className="text-xs">Email (non modifiable)</Label>
        <Input id="email" type="email" value={user.email} className="h-8 text-sm bg-gray-100" disabled />
      </div>
      <div>
        <Label htmlFor="role" className="text-xs">Statut</Label>
        <select
          id="role"
          value={role}
          onChange={e => { setRole(e.target.value as UserRole); setShowPermissions(true); }}
          className="block w-full p-2 border rounded text-sm"
        >
          <option value="admin">Administrateur</option>
          <option value="pedagogical">Responsable pédagogique</option>
          <option value="technician">Technicien</option>
        </select>
      </div>
      {showPermissions && <RolePermissionsDisplay role={role} />}
      
      <DialogFooter className="mt-4 gap-2">
        <Button type="button" variant="outline" onClick={onCancel} className="text-xs h-8">Annuler</Button>
        <Button 
          type="submit" 
          disabled={update.isPending} 
          className="text-xs h-8 bg-[#1f3d7a] hover:bg-[#2a4f94]"
        >
          {update.isPending ? "Modification…" : "Enregistrer"}
        </Button>
      </DialogFooter>
    </form>
  );
};

export default EditUserForm;
