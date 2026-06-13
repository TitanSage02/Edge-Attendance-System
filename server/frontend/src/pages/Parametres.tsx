import { useState, useEffect } from "react";
import MainLayout from "../components/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Loader2, Save, RotateCcw, Info, AlertTriangle, CheckCircle, RefreshCw } from "lucide-react";
import { useSettings } from "@/hooks/useSettings";
import { AllSettings } from "@/services/api/settings";
import ApiKeysManagement from "@/components/admin/ApiKeysManagement";

const Parametres = () => {  const {
    settings,
    systemInfo,
    loading,
    saving,
    error,
    lastUpdated,
    updatedBy,
    backups,
    loadingBackups,
    updatePartialSettings,
    resetToDefaults,
    refreshSettings,    
    refreshSystemInfo,
    createBackup,
    listBackups,
    restoreBackup
  } = useSettings();

  const [showResetDialog, setShowResetDialog] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState<string | null>(null);  const [pendingChanges, setPendingChanges] = useState<Partial<AllSettings>>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [refreshingSystemInfo, setRefreshingSystemInfo] = useState(false);

  // Gestion des changements de paramètres
  const handleSystemChange = (field: keyof AllSettings['system'], value: any) => {
    if (!settings) return;
    
    const newChanges = {
      ...pendingChanges,
      system: {
        ...pendingChanges.system,
        ...settings.system,
        [field]: value
      }
    };
    
    setPendingChanges(newChanges);
    setHasUnsavedChanges(true);
  };


  const handleBackupChange = (field: keyof AllSettings['backup'], value: any) => {
    if (!settings) return;
    
    const newChanges = {
      ...pendingChanges,
      backup: {
        ...pendingChanges.backup,
        ...settings.backup,
        [field]: value
      }
    };
    
    setPendingChanges(newChanges);
    setHasUnsavedChanges(true);
  };

  // Sauvegarde des changements
  const handleSaveChanges = async () => {
    if (!hasUnsavedChanges) return;
    
    await updatePartialSettings(pendingChanges);
    setPendingChanges({});
    setHasUnsavedChanges(false);
  };

  // Annulation des changements
  const handleCancelChanges = () => {
    setPendingChanges({});
    setHasUnsavedChanges(false);
  };

  // Remise à zéro
  const handleResetToDefaults = async () => {
    await resetToDefaults();
    setPendingChanges({});
    setHasUnsavedChanges(false);
    setShowResetDialog(false);
  };

  // Obtenir la valeur actuelle (avec les changements en attente)
  const getCurrentValue = (section: keyof AllSettings, field: string) => {
    const pendingSection = pendingChanges[section] as any;
    if (pendingSection && field in pendingSection) {
      return pendingSection[field];
    }
    return settings?.[section]?.[field as keyof AllSettings[typeof section]];
  };

  // Fonction pour gérer la restauration de sauvegarde
  const handleRestoreBackup = async () => {
    if (!selectedBackup) return;
    
    try {
      await restoreBackup(selectedBackup);
      setShowRestoreDialog(false);
      setSelectedBackup(null);
      await refreshSettings();
      await refreshSystemInfo();
    } catch (error) {
      console.error("Erreur lors de la restauration:", error);
    }
  };

  // Fonction pour créer une nouvelle sauvegarde
  const handleCreateBackup = async () => {
    try {
      await createBackup();
      await listBackups();
    } catch (error) {
      console.error("Erreur lors de la création de sauvegarde:", error);
    }
  };

  // Formatage de date
  const formatDate = (dateStr: string) => {
    const dateObj = new Date(dateStr);
    if (dateObj instanceof Date && !isNaN(dateObj.getTime())) {
      return dateObj.toLocaleString('fr-FR', {
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
    return 'Date invalide';
  };
  // Formatage de taille
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} octets`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  };

  // Fonction pour rafraîchir spécifiquement les informations système
  const handleRefreshSystemInfo = async () => {
    setRefreshingSystemInfo(true);
    try {
      await refreshSystemInfo();
    } catch (error) {
      console.error("Erreur lors du rafraîchissement des informations système:", error);
    } finally {
      setRefreshingSystemInfo(false);
    }
  };

  // Auto-actualisation des informations système toutes les 30 secondes
  useEffect(() => {
    const interval = setInterval(() => {
      if (!refreshingSystemInfo && !loading) {
        refreshSystemInfo();
      }
    }, 30000); // 30 secondes

    return () => clearInterval(interval);
  }, [refreshingSystemInfo, loading, refreshSystemInfo]);

  if (loading) {
    return (    <MainLayout requiredRoles={["admin"]}>
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Chargement des paramètres...</span>
        </div>
      </div>
    </MainLayout>
    );
  }

  if (error) {
    return (      <MainLayout requiredRoles={["admin"]}>
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <span>Erreur</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <Button onClick={refreshSettings} className="w-full">
              Réessayer
            </Button>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
    );
  }

  const systemHealth = systemInfo?.system_health || 'unknown';
  const healthColor = systemHealth === 'healthy' ? 'text-green-600' : 
                     systemHealth === 'warning' ? 'text-yellow-600' : 'text-red-600';
  return (
  <MainLayout requiredRoles={["admin"]}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-[#1f3d7a]">Paramètres</h1>
          
          <div className="flex items-center space-x-2">
            {systemInfo && (
              <Badge variant="outline" className={healthColor}>
                <CheckCircle className="h-3 w-3 mr-1" />
                Système {systemHealth}
              </Badge>
            )}
            
            {hasUnsavedChanges && (
              <Badge variant="secondary">
                <Info className="h-3 w-3 mr-1" />
                Changements non sauvegardés
              </Badge>
            )}
          </div>
        </div>

        {/* Boutons d'action */}
        {hasUnsavedChanges && (
          <Card className="bg-yellow-50 border-yellow-200">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-yellow-800">
                  Vous avez des modifications non sauvegardées.
                </p>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleCancelChanges}
                    disabled={saving}
                  >
                    Annuler
                  </Button>
                  <Button 
                    size="sm" 
                    onClick={handleSaveChanges}
                    disabled={saving}
                    className="bg-[#1f3d7a] hover:bg-[#2a4f94]"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Sauvegarde...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Sauvegarder
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        
        <Tabs defaultValue="system" className="space-y-6">         
          <TabsList>
            <TabsTrigger value="system">Système</TabsTrigger>
            <TabsTrigger value="api-keys">Clés API</TabsTrigger>
            <TabsTrigger value="backup">Sauvegarde</TabsTrigger>
            <TabsTrigger value="info">Informations</TabsTrigger>
          </TabsList>
          {/* Paramètres système */}
          <TabsContent value="system">
            <Card className="bg-white">
              <CardHeader>
                <CardTitle>Paramètres système</CardTitle>
                <CardDescription>
                  Configuration générale de l'application
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2 p-4 border-2 border-blue-100 rounded-lg bg-blue-50 mb-6">
                    <Label htmlFor="currentPromotion" className="font-bold text-lg text-blue-800">Promotion actuelle</Label>
                    <div className="flex gap-2 items-center">
                      <Input
                        id="currentPromotion"
                        value={getCurrentValue('system', 'current_promotion') || ''}
                        onChange={(e) => handleSystemChange('current_promotion', e.target.value)}
                        className="font-semibold text-lg bg-white"
                        placeholder="Ex: 2025-2026"
                      />
                    </div>
                  </div>                  
                  <div className="space-y-2">
                    <div className="space-y-2 p-4 border-2 border-blue-100 rounded-lg bg-blue-50 mb-6">
                      <Label htmlFor="maxLoginAttempts" className="font-bold text-lg text-blue-800">Seuil d'alerte d'authentification</Label>
                      <Input
                        id="maxLoginAttempts"
                        type="number"
                        min="3"
                        max="20"
                        value={getCurrentValue('system', 'max_login_attempts') || ''}
                        onChange={(e) => handleSystemChange('max_login_attempts', parseInt(e.target.value))}
                      />
                      <p className="text-xs text-muted-foreground">
                        Nombre d'échecs de certifications de présences successifs avant déclenchement d'une alerte par les modules.
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between space-x-2">
                    <Label htmlFor="notificationsEnabled">Activer les notifications</Label>
                    <Switch
                      id="notificationsEnabled"
                      checked={getCurrentValue('system', 'notifications_enabled') || false}
                      onCheckedChange={(checked) => handleSystemChange('notifications_enabled', checked)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Gestion des clés API */}
          <TabsContent value="api-keys">
            <ApiKeysManagement />
          </TabsContent>
            {/* Paramètres de sauvegarde */}
          <TabsContent value="backup">
            <Card className="bg-white">
              <CardHeader>
                <CardTitle>Sauvegarde système et restauration</CardTitle>
                <CardDescription>
                  Gestion des sauvegardes complètes du système (base de données, configuration et journaux)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="backupFrequency">Fréquence de sauvegarde (heures)</Label>
                    <Input
                      id="backupFrequency"
                      type="number"
                      min="1"
                      max="168"
                      value={getCurrentValue('backup', 'backup_frequency_hours') || ''}
                      onChange={(e) => handleBackupChange('backup_frequency_hours', parseInt(e.target.value))}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="maxBackupFiles">Nombre maximum de fichiers de sauvegarde</Label>
                    <Input
                      id="maxBackupFiles"
                      type="number"
                      min="1"
                      max="50"
                      value={getCurrentValue('backup', 'max_backup_files') || ''}
                      onChange={(e) => handleBackupChange('max_backup_files', parseInt(e.target.value))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between space-x-2">
                    <div>
                      <Label htmlFor="autoBackupEnabled">Sauvegardes automatiques</Label>
                      <p className="text-xs text-muted-foreground">
                        Active les sauvegardes automatiques selon la fréquence définie.
                      </p>
                    </div>
                    <Switch
                      id="autoBackupEnabled"
                      checked={getCurrentValue('backup', 'auto_backup_enabled') || false}
                      onCheckedChange={(checked) => handleBackupChange('auto_backup_enabled', checked)}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between space-x-2">
                    <div>
                      <Label htmlFor="includeDatabase">Inclure la base de données</Label>
                      <p className="text-xs text-muted-foreground">
                        Inclut les données SQLite dans la sauvegarde.
                      </p>
                    </div>
                    <Switch
                      id="includeDatabase"
                      checked={getCurrentValue('backup', 'include_database') || true}
                      onCheckedChange={(checked) => handleBackupChange('include_database', checked)}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between space-x-2">
                    <div>
                      <Label htmlFor="includeConfig">Inclure la configuration</Label>
                      <p className="text-xs text-muted-foreground">
                        Inclut les fichiers de configuration dans la sauvegarde.
                      </p>
                    </div>
                    <Switch
                      id="includeConfig"
                      checked={getCurrentValue('backup', 'include_config') || true}
                      onCheckedChange={(checked) => handleBackupChange('include_config', checked)}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between space-x-2">
                    <div>
                      <Label htmlFor="includeLogs">Inclure les logs</Label>
                      <p className="text-xs text-muted-foreground">
                        Inclut les fichiers journaux dans la sauvegarde.
                      </p>
                    </div>
                    <Switch
                      id="includeLogs"
                      checked={getCurrentValue('backup', 'include_logs') || false}
                      onCheckedChange={(checked) => handleBackupChange('include_logs', checked)}
                    />
                  </div>
                </div>
                
                <Separator />
  
                
                <Separator />
                
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Actions manuelles</h3>
                  
                  <div className="flex space-x-4">
                    <Button 
                      variant="outline"
                      onClick={handleCreateBackup}
                    >
                      Créer une sauvegarde système maintenant
                    </Button>
                      <Button 
                      variant="outline"
                      onClick={() => {
                        if (selectedBackup) {
                          setShowRestoreDialog(true);
                        }
                      }}
                      disabled={!selectedBackup}
                    >
                      Restaurer la sauvegarde sélectionnée
                    </Button>
                  </div>
                  
                  <div>
                    <Label htmlFor="restoreFile">Restaurer depuis un fichier de sauvegarde système</Label>
                    <div className="mt-2 flex space-x-2">
                      <Input type="file" accept=".zip,.backup" />
                      <Button variant="outline">
                        Restaurer
                      </Button>
                    </div>
                  </div>
                </div>
                  {/* Liste des sauvegardes */}
                <div className="mt-6">
                  <h3 className="text-lg font-medium">Sauvegardes système disponibles</h3>
                  
                  {loadingBackups ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin mr-2" />
                      Chargement des sauvegardes...
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {backups.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          Aucune sauvegarde système trouvée. Effectuez une sauvegarde manuelle ou attendez les sauvegardes automatiques.
                        </p>                      ) : (
                        backups.map((backup) => (
                          <Card key={backup.name || backup.path} className="hover:shadow-md transition-shadow">
                            <CardContent className="flex justify-between items-center">
                              <div>
                                <p className="text-sm font-medium">
                                  Sauvegarde système du {formatDate(backup.created_at)}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {backup.name} ({formatSize(backup.size)})
                                </p>
                                {backup.backup_type && (
                                  <p className="text-xs text-blue-600">
                                    Type: {backup.backup_type}
                                  </p>
                                )}                                {backup.includes && (
                                  <p className="text-xs text-green-600">
                                    Inclut: {Object.entries(backup.includes)
                                      .filter(([_, value]) => value === true)
                                      .map(([key, _]) => key)
                                      .join(', ')}
                                  </p>
                                )}
                              </div>
                              
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => setSelectedBackup(backup.name)}
                                className={
                                  selectedBackup === backup.name
                                  ? "bg-blue-500 text-white"
                                  : "text-blue-500"
                                }
                              >
                                {selectedBackup === backup.name ? 'Sélectionnée' : 'Sélectionner'}
                              </Button>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Informations système */}
          <TabsContent value="info">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">              <Card className="bg-white">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>État du système</CardTitle>
                      <CardDescription>
                        Informations en temps réel sur l'état de l'application
                      </CardDescription>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={handleRefreshSystemInfo}
                      disabled={refreshingSystemInfo || loading}
                    >
                      {refreshingSystemInfo ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {systemInfo ? (
                    <>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">État général:</span>
                        <Badge variant={systemInfo.system_health === 'healthy' ? 'default' : 
                                      systemInfo.system_health === 'warning' ? 'secondary' : 'destructive'}>
                          {systemInfo.system_health === 'healthy' ? '✓ Opérationnel' :
                           systemInfo.system_health === 'warning' ? '⚠ Attention' : 
                           systemInfo.system_health === 'error' ? '✗ Erreur' : systemInfo.system_health}
                        </Badge>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Version:</span>
                        <span className="text-sm font-mono">{systemInfo.version}</span>
                      </div>                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Promotion actuelle:</span>
                        <span className="text-sm font-semibold text-blue-600">{systemInfo.current_promotion}</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Base de données:</span>
                        <Badge variant={systemInfo.database_status === 'healthy' ? 'default' : 'destructive'}>
                          {systemInfo.database_status === 'healthy' ? '✓ Connectée' :
                           systemInfo.database_status === 'error' ? '✗ Erreur' : 
                           systemInfo.database_status || 'Inconnue'}
                        </Badge>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Broker MQTT:</span>
                        <Badge variant={systemInfo.mqtt_status === 'connected' ? 'default' : 
                                      systemInfo.mqtt_status === 'error' ? 'destructive' : 'secondary'}>
                          {systemInfo.mqtt_status === 'connected' ? '✓ Connecté' :
                           systemInfo.mqtt_status === 'error' ? '✗ Erreur' : 
                           systemInfo.mqtt_status === 'disconnected' ? '○ Déconnecté' :
                           systemInfo.mqtt_status || 'Inconnue'}
                        </Badge>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Notifications:</span>
                        <Badge variant={systemInfo.notifications_enabled ? 'default' : 'secondary'}>
                          {systemInfo.notifications_enabled ? '✓ Activées' : '✗ Désactivées'}
                        </Badge>
                      </div>
                      
                      {systemInfo.last_backup && (
                        <div className="flex justify-between">
                          <span className="text-sm font-medium">Dernière sauvegarde:</span>
                          <span className="text-sm">{formatDate(systemInfo.last_backup)}</span>
                        </div>
                      )}

                      <div className="pt-2 border-t">
                        <div className="flex items-center text-xs text-muted-foreground">
                          <Info className="h-3 w-3 mr-1" />
                          Actualisation automatique toutes les 30 secondes
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="flex items-center justify-center py-8">
                      <div className="text-center">
                        <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">
                          Impossible de charger les informations système
                        </p>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={handleRefreshSystemInfo}
                          disabled={refreshingSystemInfo}
                          className="mt-2"
                        >
                          {refreshingSystemInfo ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Chargement...
                            </>
                          ) : (
                            <>
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Réessayer
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              <Card className="bg-white">
                <CardHeader>
                  <CardTitle>Actions avancées</CardTitle>
                  <CardDescription>
                    Opérations de maintenance et de configuration
                  </CardDescription>
                </CardHeader>                <CardContent className="space-y-4">
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={refreshSettings}
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <RotateCcw className="h-4 w-4 mr-2" />
                    )}
                    Actualiser les paramètres
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={handleRefreshSystemInfo}
                    disabled={refreshingSystemInfo}
                  >
                    {refreshingSystemInfo ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Actualiser les informations système
                  </Button>
                  
                  <Button 
                    variant="destructive" 
                    className="w-full justify-start"
                    onClick={() => setShowResetDialog(true)}
                    disabled={saving}
                  >
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Remettre aux valeurs par défaut
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* Informations de dernière mise à jour */}
        {(lastUpdated || updatedBy) && (
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="pt-4">
              <div className="flex items-center space-x-4 text-sm text-blue-800">
                {lastUpdated && (
                  <span>
                    Dernière mise à jour: {new Date(lastUpdated).toLocaleString('fr-FR')}
                  </span>
                )}
                {updatedBy && (
                  <span>
                    Par: {updatedBy}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        )}        {/* Dialog de confirmation pour la remise à zéro */}
        <ConfirmationDialog
          isOpen={showResetDialog}
          onClose={() => setShowResetDialog(false)}
          onConfirm={handleResetToDefaults}
          title="Confirmer la remise à zéro"
          description="Êtes-vous sûr de vouloir remettre tous les paramètres aux valeurs par défaut ? Cette action est irréversible et tous les paramètres personnalisés seront perdus."
        />
          {/* Dialog de confirmation pour la restauration */}
        <ConfirmationDialog
          isOpen={showRestoreDialog}
          onClose={() => setShowRestoreDialog(false)}
          onConfirm={handleRestoreBackup}
          title="Confirmer la restauration système"
          description={`ATTENTION: Vous êtes sur le point de restaurer la sauvegarde système ${selectedBackup || ''}. Cette opération remplacera la base de données et les fichiers de configuration actuels. Voulez-vous continuer?`}
        />
      </div>
    </MainLayout>
  );
};

export default Parametres;
