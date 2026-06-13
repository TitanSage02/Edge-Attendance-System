import { Navigate } from "react-router-dom";
import MainLayout from "@/components/layout/MainLayout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { ProfileInfo } from "@/components/profile/ProfileInfo";
import { PasswordChangeForm } from "@/components/profile/PasswordChangeForm";

import { authApi } from "@/services/api/auth";
import { useAuth } from "@/hooks/useAuth";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { User } from "@/types/userTypes";

const Profile = () => {
  const { user, isAuthenticated, updateProfile } = useAuth();
  const { success, error } = useUnifiedToast();

  // Si pas connecté, on renvoie sur /login
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  // Traduction du rôle en français
  const getRoleName = (role: string) => {
    switch (role) {
      case "admin":
        return "Administrateur";
      case "pedagogical":
        return "Responsable pédagogique";
      case "technician":
        return "Technicien";
      default:
        return role;
    }
  };

  // Mise à jour des infos de profil
  const handleUpdateProfile = async (
    firstName: string,
    lastName: string,
    email: string
  ) => {
    try {
      await updateProfile({ firstName, lastName, email });      success("Votre profil a été mis à jour avec succès.", { title: "Profil mis à jour" });
    } catch (err: unknown) {      error("Impossible de mettre à jour le profil.", { title: "Erreur" });
    }
  };
  // Mise à jour du mot de passe
  const handleUpdatePassword = async (
    currentPassword: string,
    newPassword: string,
    confirmPassword: string
  ) => {
    if (newPassword !== confirmPassword) {     
      error("Les deux mots de passe ne correspondent pas.", { title: "Erreur" });
      return;
    }

    try {
      await authApi.changePassword({ currentPassword, newPassword });      
      success("Votre mot de passe a été mis à jour avec succès.", { title: "Mot de passe mis à jour" });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || "Impossible de mettre à jour le mot de passe.";      
      error(errorMessage, { title: "Erreur" });
    }
  };

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6 text-[#1f3d7a]">Mon profil</h1>

        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="profile">
              Informations personnelles
            </TabsTrigger>
            <TabsTrigger value="security">Sécurité</TabsTrigger>
          </TabsList>          
          <TabsContent value="profile">
            <ProfileInfo
              user={user}
              getRoleName={getRoleName}
              onUpdateProfile={handleUpdateProfile}
            />
          </TabsContent>

          <TabsContent value="security">
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-lg text-[#1f3d7a]">
                  Mot de passe
                </CardTitle>
                <CardDescription>
                  Mettez à jour votre mot de passe pour sécuriser votre compte.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PasswordChangeForm onSubmit={handleUpdatePassword} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
};

export default Profile;