import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { User } from "@/types/userTypes";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { authApi } from "@/services/api/auth";
import { Loader2 } from "lucide-react";

interface ProfilePhotoProps {
  user: User;
  getRoleName: (role: string) => string;
  onAvatarUpdate: (user: User) => void;
}

export const ProfilePhoto = ({ user, getRoleName, onAvatarUpdate }: ProfilePhotoProps) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { error, success } = useUnifiedToast();

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;    // Vérifier le type de fichier
    if (!file.type.startsWith('image/')) {
      error("Le fichier doit être une image", { title: "Erreur" });
      return;
    }

    // Vérifier la taille du fichier (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      error("L'image ne doit pas dépasser 2MB", { title: "Erreur" });
      return;
    }

    try {
      setIsUploading(true);
      const formData = new FormData();
      formData.append('file', file);      const response = await authApi.uploadAvatar(formData);
      onAvatarUpdate(response.user);
      
      success("Photo de profil mise à jour", { title: "Succès" });
    } catch (uploadError) {
      error("Impossible de mettre à jour la photo de profil", { title: "Erreur" });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteAvatar = async () => {
    try {
      setIsDeleting(true);      const response = await authApi.deleteAvatar();
      onAvatarUpdate(response.user);
      
      success("Photo de profil supprimée", { title: "Succès" });
    } catch (deleteError) {
      error("Impossible de supprimer la photo de profil", { title: "Erreur" });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="text-lg text-[#1f3d7a]">Photo de profil</CardTitle>
        <CardDescription>Personnalisez votre photo de profil</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
        {user.avatar ? (
          <div className="relative">
            <img
              src={`${import.meta.env.VITE_API_URL}/api/v1/auth/profile/avatar/${user.id}`}
              alt="Profile"
              className="w-24 h-24 rounded-full object-cover border-2 border-[#1f3d7a]"
            />
            <div className="absolute -top-2 -right-2 bg-[#1f3d7a] text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
              {getRoleName(user.role).charAt(0)}
            </div>
          </div>
        ) : (
          <div className="w-24 h-24 rounded-full bg-[#1f3d7a]/10 flex items-center justify-center text-[#1f3d7a] font-bold text-2xl border-2 border-[#1f3d7a]/20">
            {user.firstName.charAt(0)}{user.lastName.charAt(0)}
          </div>
        )}
        <div className="flex flex-col items-center sm:items-start">
          <p className="text-sm text-gray-500 mb-4">
            Téléchargez une photo JPG ou PNG. Recommandé : 400x400px, max 2MB.
          </p>
          <div className="flex gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*"
              className="hidden"
            />
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isDeleting}
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Téléchargement...
                </>
              ) : (
                "Parcourir"
              )}
            </Button>
            {user.avatar && (
              <Button 
                variant="ghost" 
                size="sm"
                onClick={handleDeleteAvatar}
                disabled={isUploading || isDeleting}
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Suppression...
                  </>
                ) : (
                  "Supprimer"
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
