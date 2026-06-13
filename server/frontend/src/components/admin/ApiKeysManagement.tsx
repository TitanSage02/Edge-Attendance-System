import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { 
  Loader2, 
  Plus, 
  Key, 
  Copy, 
  Eye, 
  EyeOff, 
  Shield, 
  ShieldOff, 
  Trash2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock
} from "lucide-react";
import { useApiKeys } from "@/hooks/useApiKeys";
import { ApiKeyCreate } from "@/services/api/apiKeys";
import { useToast } from "@/hooks/use-toast";

const ApiKeysManagement = () => {
  const {
    apiKeys,
    loading,
    creating,
    error,
    lastCreatedKey,
    createApiKey,
    revokeApiKey,
    activateApiKey,
    deleteApiKey,
    clearLastCreatedKey,
    clearError,
    loadApiKeys
  } = useApiKeys();

  const { toast } = useToast();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newModuleUid, setNewModuleUid] = useState("");
  const [showNewKey, setShowNewKey] = useState(false);
  const [copiedKeyId, setCopiedKeyId] = useState<number | null>(null);

  // Créer une nouvelle clé API
  const handleCreateApiKey = async () => {
    if (!newModuleUid.trim()) {
      toast({
        title: "Erreur",
        description: "Veuillez saisir l'UID du module",
        variant: "destructive",
      });
      return;
    }

    const moduleUid = parseInt(newModuleUid.trim());
    if (isNaN(moduleUid) || moduleUid <= 0) {
      toast({
        title: "Erreur",
        description: "L'UID du module doit être un nombre entier positif",
        variant: "destructive",
      });
      return;
    }

    const data: ApiKeyCreate = { module_uid: moduleUid };
    const result = await createApiKey(data);
    
    if (result) {
      setShowCreateDialog(false);
      setNewModuleUid("");
      setShowNewKey(true);
      toast({
        title: "Clé API créée",
        description: `Clé API créée avec succès pour le module ${moduleUid}`,
      });
    }
  };

  // Copier la clé dans le presse-papier
  const copyToClipboard = async (key: string, keyId?: number) => {
    try {
      await navigator.clipboard.writeText(key);
      
      if (keyId) {
        setCopiedKeyId(keyId);
        setTimeout(() => setCopiedKeyId(null), 2000);
      }
      
      toast({
        title: "Copié !",
        description: "La clé API a été copiée dans le presse-papier",
      });
    } catch (err) {
      toast({
        title: "Erreur",
        description: "Impossible de copier la clé",
        variant: "destructive",
      });
    }
  };

  // Révoquer une clé API
  const handleRevokeKey = async (keyId: number, moduleUid: number) => {
    const success = await revokeApiKey(keyId);
    if (success) {
      toast({
        title: "Clé révoquée",
        description: `Clé API du module ${moduleUid} révoquée avec succès`,
      });
    }
  };

  // Activer une clé API
  const handleActivateKey = async (keyId: number, moduleUid: number) => {
    const success = await activateApiKey(keyId);
    if (success) {
      toast({
        title: "Clé activée",
        description: `Clé API du module ${moduleUid} activée avec succès`,
      });
    }
  };

  // Supprimer une clé API
  const handleDeleteKey = async (keyId: number, moduleUid: number) => {
    const success = await deleteApiKey(keyId);
    if (success) {
      toast({
        title: "Clé supprimée",
        description: `Clé API du module ${moduleUid} supprimée définitivement`,
      });
    }
  };

  // Fermer le dialog de nouvelle clé
  const handleCloseNewKeyDialog = () => {
    setShowNewKey(false);
    clearLastCreatedKey();
  };

  // Formater la date
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <Card className="bg-white">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Key className="h-5 w-5" />
              <span>Gestion des clés API</span>
            </CardTitle>
            <CardDescription>
              Gestion des clés d'authentification pour les modules de pointage
            </CardDescription>
          </div>
          
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#1f3d7a] hover:bg-[#2a4f94]">
                <Plus className="h-4 w-4 mr-2" />
                Nouvelle clé
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Créer une nouvelle clé API</DialogTitle>
                <DialogDescription>
                  Générez une clé API sécurisée pour un module de pointage
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="moduleUid">UID du module de pointage</Label>
                  <Input
                    id="moduleUid"
                    type="number"
                    placeholder="Ex: 1001"
                    value={newModuleUid}
                    onChange={(e) => setNewModuleUid(e.target.value)}
                    min="1"
                  />
                  <p className="text-xs text-muted-foreground">
                    Identifiant unique du module de pointage (nombre entier)
                  </p>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateDialog(false)}
                  disabled={creating}
                >
                  Annuler
                </Button>
                <Button
                  onClick={handleCreateApiKey}
                  disabled={creating}
                  className="bg-[#1f3d7a] hover:bg-[#2a4f94]"
                >
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Création...
                    </>
                  ) : (
                    <>
                      <Key className="h-4 w-4 mr-2" />
                      Créer la clé
                    </>
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Affichage des erreurs */}
        {error && (
          <Card className="bg-red-50 border-red-200">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <p className="text-sm text-red-800">{error}</p>
                </div>
                <Button variant="outline" size="sm" onClick={clearError}>
                  Fermer
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Liste des clés API */}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Chargement des clés API...</span>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {apiKeys.length === 0 ? (
              <div className="text-center py-8">
                <Key className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-sm text-muted-foreground">
                  Aucune clé API trouvée. Créez votre première clé pour commencer.
                </p>
              </div>
            ) : (
              apiKeys.map((apiKey) => (
                <Card key={apiKey.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="font-mono">
                            Module {apiKey.module_uid}
                          </Badge>
                          <Badge 
                            variant={apiKey.is_active ? "default" : "secondary"}
                            className={apiKey.is_active ? "bg-green-500" : "bg-gray-500"}
                          >
                            {apiKey.is_active ? (
                              <>
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Active
                              </>
                            ) : (
                              <>
                                <XCircle className="h-3 w-3 mr-1" />
                                Révoquée
                              </>
                            )}
                          </Badge>
                        </div>
                        
                        <div className="text-sm text-muted-foreground space-y-1">
                          <div className="flex items-center space-x-4">
                            <span>Créée le {formatDate(apiKey.created_at)}</span>
                            {apiKey.last_used_at && (
                              <span className="flex items-center space-x-1">
                                <Clock className="h-3 w-3" />
                                <span>Dernière utilisation: {formatDate(apiKey.last_used_at)}</span>
                              </span>
                            )}
                          </div>
                          <div className="font-mono text-xs bg-gray-100 px-2 py-1 rounded flex items-center justify-between">
                            <span className="truncate mr-2">{apiKey.key}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard(apiKey.key, apiKey.id)}
                              className="h-6 w-6 p-0 flex-shrink-0"
                            >
                              {copiedKeyId === apiKey.id ? (
                                <CheckCircle className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {apiKey.is_active ? (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="outline" size="sm">
                                <ShieldOff className="h-4 w-4 mr-1" />
                                Révoquer
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Révoquer la clé API</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Êtes-vous sûr de vouloir révoquer cette clé API ? 
                                  Le module {apiKey.module_uid} ne pourra plus s'authentifier 
                                  avec cette clé.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Annuler</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleRevokeKey(apiKey.id, apiKey.module_uid)}
                                  className="bg-red-600 hover:bg-red-700"
                                >
                                  Révoquer
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleActivateKey(apiKey.id, apiKey.module_uid)}
                          >
                            <Shield className="h-4 w-4 mr-1" />
                            Activer
                          </Button>
                        )}
                        
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                              <Trash2 className="h-4 w-4 mr-1" />
                              Supprimer
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Supprimer définitivement</AlertDialogTitle>
                              <AlertDialogDescription>
                                Êtes-vous sûr de vouloir supprimer définitivement cette clé API ?
                                Cette action est irréversible.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Annuler</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteKey(apiKey.id, apiKey.module_uid)}
                                className="bg-red-600 hover:bg-red-700"
                              >
                                Supprimer
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
            
            {/* <div className="flex justify-center pt-4">
              <Button
                variant="outline"
                onClick={() => loadApiKeys(true)}
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Eye className="h-4 w-4 mr-2" />
                )}
                Inclure les clés révoquées
              </Button>
            </div> */}
          </div>
        )}
      </CardContent>

      {/* Dialog pour afficher la nouvelle clé créée */}
      <Dialog open={showNewKey} onOpenChange={handleCloseNewKeyDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>Clé API créée avec succès</span>
            </DialogTitle>
            <DialogDescription>
              Votre nouvelle clé API a été générée.
            </DialogDescription>
          </DialogHeader>
          
          {lastCreatedKey && (
            <div className="space-y-4 py-4">          
              <div className="space-y-2">
                <Label>Clé API pour le module {lastCreatedKey.module_uid}</Label>
                <div className="flex items-center space-x-2">
                  <Input
                    readOnly
                    value={lastCreatedKey.key}
                    className="font-mono text-sm"
                  />
                  <Button
                    onClick={() => copyToClipboard(lastCreatedKey.key)}
                    size="sm"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Copier
                  </Button>
                </div>
              </div>
              
              <Separator />
              
              <div className="text-xs text-muted-foreground space-y-1">
                <p><strong>Module:</strong> {lastCreatedKey.module_uid}</p>
                <p><strong>Créée le:</strong> {formatDate(lastCreatedKey.created_at)}</p>
                <p><strong>Statut:</strong> {lastCreatedKey.is_active ? "Active" : "Inactive"}</p>
              </div>
            </div>
          )}
          
          <div className="flex justify-end">
            <Button onClick={handleCloseNewKeyDialog}>
              J'ai copié la clé
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default ApiKeysManagement;
