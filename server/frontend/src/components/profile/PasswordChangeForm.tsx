import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/ui/password-input";
import { PasswordRequirements } from "@/components/ui/password-requirements";
import { PasswordStrengthIndicator } from "@/components/ui/password-strength-indicator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { changePasswordSchema, type ChangePasswordFormData } from "@/schemas/authSchemas";
import { z } from "zod";

interface PasswordChangeFormProps {
  onSubmit: (currentPassword: string, newPassword: string, confirmPassword: string) => void;
}

export const PasswordChangeForm = ({ onSubmit }: PasswordChangeFormProps) => {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");  const [errors, setErrors] = useState<Partial<ChangePasswordFormData>>({});
  const [isOpen, setIsOpen] = useState(false);
  // Validation automatique à chaque changement d'état
  useEffect(() => {
    if (currentPassword || newPassword || confirmPassword) {
      validateCurrentState();
    }
  }, [currentPassword, newPassword, confirmPassword]);

  // Validation de l'état actuel
  const validateCurrentState = () => {
    const formData: ChangePasswordFormData = {
      currentPassword,
      newPassword,
      confirmPassword
    };

    try {
      changePasswordSchema.parse(formData);
      
      // Si la validation réussit, effacer toutes les erreurs
      setErrors({});
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Partial<ChangePasswordFormData> = {};
        
        // Grouper les erreurs par champ pour éviter les doublons
        const errorsByField: Record<string, string[]> = {};
        error.errors.forEach(err => {
          if (err.path.length > 0) {
            const name = err.path[0] as string;
            if (['currentPassword', 'newPassword', 'confirmPassword'].includes(name)) {
              if (!errorsByField[name]) {
                errorsByField[name] = [];
              }
              errorsByField[name].push(err.message);
            }
          }
        });
        
        // Prendre seulement la première erreur par champ
        Object.entries(errorsByField).forEach(([field, messages]) => {
          fieldErrors[field as keyof ChangePasswordFormData] = messages[0];
        });
          setErrors(fieldErrors);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const formData: ChangePasswordFormData = {
      currentPassword,
      newPassword,
      confirmPassword
    };

    try {
      // Validation complète avec Zod
      changePasswordSchema.parse(formData);
      
      // Si la validation réussit, réinitialiser les erreurs
      setErrors({});
      
      // Soumettre les modifications
      onSubmit(currentPassword, newPassword, confirmPassword);
      
      // Réinitialiser le formulaire et fermer la boîte de dialogue
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setIsOpen(false);
    } catch (error) {
      if (error instanceof z.ZodError) {
        // Transformer les erreurs Zod en objet d'erreurs par champ
        const fieldErrors: Partial<ChangePasswordFormData> = {};
        error.errors.forEach(err => {
          if (err.path.length > 0) {
            const fieldName = err.path[0] as keyof ChangePasswordFormData;
            fieldErrors[fieldName] = err.message;
          }
        });
        setErrors(fieldErrors);
      }
    }
  };    
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6">
        <div>
          <Label htmlFor="current-password">Mot de passe actuel</Label>            <PasswordInput
              id="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              error={errors.currentPassword}
              className="mt-1"
              placeholder="Saisissez votre mot de passe actuel"
            />
          {errors.currentPassword && (
            <p className="text-red-500 text-sm mt-1">{errors.currentPassword}</p>
          )}
        </div>
        
        <div className="space-y-4">
          <div>
            <Label htmlFor="new-password">Nouveau mot de passe</Label>            <PasswordInput
              id="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              error={errors.newPassword}
              className="mt-1"
              placeholder="Saisissez votre nouveau mot de passe"
            />
            {errors.newPassword && (
              <p className="text-red-500 text-sm mt-1">{errors.newPassword}</p>
            )}
          </div>          
          {/* Indicateur de force et exigences en temps réel */}
          {newPassword && (
            <div className="space-y-3">
              <PasswordStrengthIndicator password={newPassword} />
              <PasswordRequirements 
                password={newPassword} 
                className="bg-gray-50 p-4 rounded-lg"
              />
            </div>
          )}
        </div>
        
        <div>
          <Label htmlFor="confirm-password">Confirmer le mot de passe</Label>          <PasswordInput
            id="confirm-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            className="mt-1"
            placeholder="Confirmez votre nouveau mot de passe"
          />
          {errors.confirmPassword && (
            <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
          )}
        </div>
      </div>      
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button 
            className="bg-[#1f3d7a] hover:bg-[#162c58] w-full sm:w-auto"
            disabled={!currentPassword || !newPassword || !confirmPassword || Object.keys(errors).length > 0}
          >
            Modifier le mot de passe
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmer le changement de mot de passe</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir changer votre mot de passe ? Cette action est irréversible.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleSubmit}>Confirmer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
