import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { useUsers } from "@/hooks/useUsers";
import RolePermissionsDisplay from "./RolePermissionsDisplay";
import { UserRole } from "@/types/userTypes";
import { DialogFooter } from "@/components/ui/dialog";

interface Props {
  onSuccess: () => void;
  onCancel: () => void;
}

const AddUserForm = ({ onSuccess, onCancel }: Props) => {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("technician");  const [showPermissions, setShowPermissions] = useState(false);
  const { success, error } = useUnifiedToast();
  const { create } = useUsers();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();    try {
      await create.mutateAsync({ firstName, lastName, email, role });
      success("Utilisateur créé et email envoyé", { title: "Succès" });
      onSuccess();
    } catch (createError) {
      error(createError instanceof Error ? createError.message : "Erreur lors de la création", { title: "Erreur" });
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
        <Label htmlFor="email" className="text-xs">Email</Label>
        <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} className="h-8 text-sm" required />
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
      {showPermissions && <RolePermissionsDisplay role={role} />}      <DialogFooter className="mt-4 gap-2">
        <Button type="button" variant="outline" onClick={onCancel} className="text-xs h-8">Annuler</Button>
        <Button type="submit" disabled={create.isPending} className="text-xs h-8 bg-[#1f3d7a] hover:bg-[#2a4f94]">
          {create.isPending ? "Création…" : "Ajouter"}
        </Button>
      </DialogFooter>
    </form>
  );
};

export default AddUserForm;