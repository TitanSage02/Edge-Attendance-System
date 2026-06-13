import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { configService } from '@/services/config';
import { CheckCircle, XCircle, RefreshCw, Settings, Globe, Wifi, CloudCog } from 'lucide-react';
import { Switch } from '@/components/ui/switch';

// Vérifie si une URL d'API est définie dans les variables d'environnement (pour Vercel ou .env)
const hasEnvApiUrl = !!import.meta.env.VITE_API_URL;

interface ConnectionStatus {
  api: boolean;
  mqtt: boolean;
  loading: boolean;
}

export const ConfigurationPanel: React.FC = () => {
  const [apiUrl, setApiUrl] = useState(configService.apiUrl);
  const [useEnvUrl, setUseEnvUrl] = useState(!localStorage.getItem('CREC_API_URL') && hasEnvApiUrl);
  const [status, setStatus] = useState<ConnectionStatus>({
    api: false,
    mqtt: false,
    loading: false
  });
  const [message, setMessage] = useState<string>('');

  // Test de la connexion API
  const testApiConnection = async () => {
    setStatus(prev => ({ ...prev, loading: true }));
    try {
      const isConnected = await configService.validateApiConnection();
      setStatus(prev => ({ ...prev, api: isConnected }));
      
      if (isConnected) {
        setMessage('✅ Connexion API réussie');
      } else {
        setMessage('❌ Connexion API échouée');
      }
    } catch (error) {
      setStatus(prev => ({ ...prev, api: false }));
      setMessage('❌ Erreur lors du test de connexion API');
    } finally {
      setStatus(prev => ({ ...prev, loading: false }));
    }
  };
  // Sauvegarde de la configuration
  const saveConfiguration = () => {
    if (useEnvUrl && hasEnvApiUrl) {
      // Si on utilise l'URL de l'environnement, supprimer l'URL locale
      localStorage.removeItem('CREC_API_URL');
      configService.setApiUrl(null, true); // Utiliser l'URL de Vercel
      setMessage('💾 Configuration sauvegardée - Utilisation de l\'URL définie dans Vercel');
    } else {
      // Sinon, utiliser l'URL personnalisée
      // Nettoyer l'URL avant de la sauvegarder
      const cleanedUrl = cleanApiUrl(apiUrl);
      
      if (cleanedUrl !== apiUrl) {
        setApiUrl(cleanedUrl);
      }
      
      configService.setApiUrl(cleanedUrl, false);
      localStorage.setItem('CREC_API_URL', cleanedUrl);
      setMessage('💾 Configuration sauvegardée localement');
    }
    
    // Recharger la page pour appliquer les changements
    setTimeout(() => {
      window.location.reload();
    }, 1500);
  };
  // Nettoie les URL (supprime les barres obliques finales, assure que "/api/v1" est présent)
  const cleanApiUrl = (url: string): string => {
    // Ajouter le protocole si manquant
    let cleanUrl = url.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = `http://${cleanUrl}`;
    }
    
    // S'assurer que l'URL se termine par "/api/v1"
    cleanUrl = cleanUrl.replace(/\/*$/, ''); // Supprimer les barres obliques finales
    if (!cleanUrl.endsWith('/api/v1')) {
      // Si l'URL contient déjà /api/ mais pas /api/v1, ajuster
      if (cleanUrl.includes('/api/')) {
        cleanUrl = cleanUrl.replace(/\/api\/.*$/, '/api/v1');
      } else {
        cleanUrl = `${cleanUrl}/api/v1`;
      }
    }
    
    return cleanUrl;
  };
  // Réinitialisation aux valeurs par défaut
  const resetToDefaults = () => {
    const defaultUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    setApiUrl(defaultUrl);
    localStorage.removeItem('CREC_API_URL');
    localStorage.removeItem('CREC_MQTT_URL');
    // Priorité à l'URL de Vercel si elle existe
    if (hasEnvApiUrl) {
      setUseEnvUrl(true);
    }
    setMessage('🔄 Configuration réinitialisée');
  };
  // Chargement de la configuration depuis localStorage
  useEffect(() => {
    const savedApiUrl = localStorage.getItem('CREC_API_URL');
    const savedMqttUrl = localStorage.getItem('CREC_MQTT_URL');
    
    if (savedApiUrl) {
      // Si une configuration locale existe, l'utiliser
      setApiUrl(savedApiUrl);
      setUseEnvUrl(false); // Désactive l'option Vercel puisqu'on a une config locale
    } else if (import.meta.env.VITE_API_URL) {
      // Sinon, utiliser la configuration Vercel si disponible
      setApiUrl(import.meta.env.VITE_API_URL);
      setUseEnvUrl(true);
    }
    
    // Test initial de connexion
    testApiConnection();
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configuration Frontend
          </CardTitle>
          <CardDescription>
            Configurez les URLs des services backend pour l'application Edge Attendance System
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Configuration API */}
          <div className="space-y-2">
            <Label htmlFor="api-url" className="flex items-center gap-2">
              <Globe className="h-4 w-4" />
              URL de l'API Backend
            </Label>
            <div className="flex flex-col space-y-2">
              <div className="flex gap-2">
                <Input
                  id="api-url"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8000/api/v1"
                  className="flex-1"
                  disabled={useEnvUrl && hasEnvApiUrl}
                  onBlur={(e) => {
                    const cleanedUrl = cleanApiUrl(e.target.value);
                    if (cleanedUrl !== e.target.value) {
                      setApiUrl(cleanedUrl);
                    }
                  }}
                />
                <Button
                  onClick={testApiConnection}
                  disabled={status.loading}
                  variant="outline"
                  size="sm"
                  title="Tester la connexion"
                >
                  {status.loading ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : status.api ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">
                {useEnvUrl && hasEnvApiUrl 
                  ? "URL configurée dans Vercel/environnement" 
                  : "Format attendu: http(s)://adresse-ip-ou-nom-domaine:port/api/v1"}
              </div>
            </div>
          </div>
          {/* Option d'URL depuis Vercel ou .env */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="use-env-url" className="flex items-center gap-2">
                <CloudCog className="h-4 w-4" />
                Utiliser l'URL de l'API depuis Vercel ou .env
              </Label>
              <Switch
                id="use-env-url"
                checked={useEnvUrl}
                disabled={!hasEnvApiUrl}
                onCheckedChange={(checked) => {
                  setUseEnvUrl(checked);
                  if (checked && hasEnvApiUrl) {
                    setApiUrl(import.meta.env.VITE_API_URL);
                  } else {
                    setApiUrl(configService.apiUrl);
                  }
                }}
              />
            </div>
            
            {/* Informations sur la configuration Vercel */}
            <div className="text-xs text-muted-foreground border-l-2 border-blue-200 pl-2 ml-2">
              {hasEnvApiUrl ? (
                <>URL de l'API configurée dans Vercel: <code className="bg-gray-100 px-1 rounded">{import.meta.env.VITE_API_URL}</code></>
              ) : (
                <>Pour configurer l'URL API dans Vercel, ajoutez la variable <code className="bg-gray-100 px-1 rounded">VITE_API_URL</code> dans les paramètres du projet.</>
              )}
            </div>
          </div>

          {/* État actuel */}
          <div className="flex gap-2">
            <Badge variant={status.api ? "success" : "destructive"}>
              API: {status.api ? "Connecté" : "Déconnecté"}
            </Badge>
            <Badge variant="secondary">
              Mode: {configService.isDevMode ? "Développement" : "Production"}
            </Badge>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-4">
            <Button onClick={saveConfiguration} className="flex-1">
              💾 Sauvegarder Configuration
            </Button>
            <Button onClick={resetToDefaults} variant="outline">
              🔄 Réinitialiser
            </Button>
          </div>

          {/* Message de statut */}
          {message && (
            <Alert>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Informations de débogage */}
      {configService.isDebugMode && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Informations de débogage</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
              {JSON.stringify(configService.getConfig(), null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ConfigurationPanel;
