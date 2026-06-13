import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User } from "@/types/userTypes";
import { formatLastLogin } from "@/utils/dateUtils";

interface ProfileInfoProps {
  user: User;
  getRoleName: (role: string) => string;
  onUpdateProfile: (firstName: string, lastName: string, email: string) => void;
}

export const ProfileInfo = ({ user, getRoleName, onUpdateProfile }: ProfileInfoProps) => {
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [firstName, setFirstName] = useState(user.firstName);
  const [lastName, setLastName] = useState(user.lastName);
  const [email, setEmail] = useState(user.email);

  const handleSubmit = () => {
    onUpdateProfile(firstName, lastName, email);
    setIsEditingProfile(false);
  };

  return (
    <Card className="bg-white">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg text-[#1f3d7a]">Informations personnelles</CardTitle>
            <CardDescription>Gérez vos informations personnelles</CardDescription>
          </div>
          <Button
            variant="outline"
            onClick={() => setIsEditingProfile(!isEditingProfile)}
          >
            {isEditingProfile ? "Annuler" : "Modifier"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <Label htmlFor="firstName">Prénom</Label>
            {isEditingProfile ? (
              <Input
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="mt-1"
              />
            ) : (
              <p className="text-gray-700 mt-1">{user.firstName}</p>
            )}
          </div>
          <div>
            <Label htmlFor="lastName">Nom</Label>
            {isEditingProfile ? (
              <Input
                id="lastName"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="mt-1"
              />
            ) : (
              <p className="text-gray-700 mt-1">{user.lastName}</p>
            )}
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
              <p className="text-gray-700 mt-1">{user.email}</p>
          </div>
          <div>
            <Label htmlFor="role">Statut</Label>
            <p className="text-gray-700 mt-1">{getRoleName(user.role)}</p>
          </div>
          <div>
            <Label htmlFor="lastLogin">Dernière connexion</Label>
            <p className="text-gray-700 mt-1">
              {typeof user.lastLogin === 'string' || user.lastLogin instanceof Date 
                ? formatLastLogin(user.lastLogin) 
                : 'Non disponible'}
            </p>
          </div>
        </div>
        
        {isEditingProfile && (
          <div className="flex justify-end mt-6">
            <Button onClick={handleSubmit}>
              Enregistrer les modifications
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
