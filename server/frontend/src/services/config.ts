/**
 * Configuration de l'application frontend Edge Attendance System
 * Gestion des variables d'environnement et de la configuration
 */

interface Config {
  API_URL: string;
  DEV_MODE: boolean;
  DEBUG: boolean;
  API_TIMEOUT: number;
  API_LONG_TIMEOUT: number;
  API_HEAVY_TIMEOUT: number;
}

class ConfigService {
  private config: Config;
  constructor() {
    this.config = {
      API_URL: import.meta.env.VITE_API_URL,
      DEV_MODE: import.meta.env.VITE_DEV_MODE === "true",
      DEBUG: import.meta.env.VITE_DEBUG === "true",
      API_TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT) || 60000,
      API_LONG_TIMEOUT: parseInt(import.meta.env.VITE_API_LONG_TIMEOUT) || 180000,
      API_HEAVY_TIMEOUT: parseInt(import.meta.env.VITE_API_HEAVY_TIMEOUT) || 300000,
    };

    // Vérification en mode développement
    if (this.config.DEV_MODE && this.config.DEBUG) {
      console.log("🔧 Configuration Frontend Edge Attendance System:", this.config);
    }
  }
  /**
   * Obtient l'URL de base de l'API
   * Priorité: localStorage > variables d'environnement > valeur par défaut
   */
  get apiUrl(): string {
    const savedApiUrl = localStorage.getItem('CREC_API_URL');
    // Si l'URL est dans le localStorage, la priorité lui est donnée
    // Si le localStorage n'a pas d'URL, utiliser la variable d'environnement (Vercel)
    // Sinon, utiliser l'URL par défaut (localhost)
    return savedApiUrl || this.config.API_URL || "http://localhost:8000/api/v1";
  }


  /**
   * Vérifie si on est en mode développement
   */
  get isDevMode(): boolean {
    return this.config.DEV_MODE;
  }

  /**
   * Vérifie si le débogage est activé
   */
  get isDebugMode(): boolean {
    return this.config.DEBUG;
  }

  /**
   * Obtient le timeout par défaut pour les requêtes API
   */
  get apiTimeout(): number {
    return this.config.API_TIMEOUT;
  }

  /**
   * Obtient le timeout pour les opérations longues
   */
  get longTimeout(): number {
    return this.config.API_LONG_TIMEOUT;
  }

  /**
   * Obtient le timeout pour les opérations très longues
   */
  get heavyTimeout(): number {
    return this.config.API_HEAVY_TIMEOUT;
  }
  /**
   * Met à jour l'URL de l'API dynamiquement
   * @param newUrl Nouvelle URL de l'API (si null, utilise l'URL de l'environnement)
   * @param useVercelUrl Si true, utilise l'URL de Vercel et ignore newUrl
   */
  setApiUrl(newUrl: string | null, useVercelUrl: boolean = false): void {
    if (useVercelUrl && import.meta.env.VITE_API_URL) {
      // Utiliser l'URL de Vercel si demandé et disponible
      this.config.API_URL = import.meta.env.VITE_API_URL;
      if (this.config.DEBUG) {
        console.log("🔄 URL API mise à jour depuis Vercel:", this.config.API_URL);
      }
    } else if (newUrl) {
      // Utiliser l'URL fournie
      this.config.API_URL = newUrl;
      if (this.config.DEBUG) {
        console.log("🔄 URL API mise à jour manuellement:", newUrl);
      }
    }
  }

  /**
   * Obtient toute la configuration
   */
  getConfig(): Config {
    return { ...this.config };
  }

  /**
   * Affiche l'état actuel de la configuration
   */
  logConfig(): void {
    console.group("🔧 Configuration Edge Attendance System Frontend");
    console.log("API URL:", this.config.API_URL);
    console.log("Mode développement:", this.config.DEV_MODE);
    console.log("Débogage activé:", this.config.DEBUG);
    console.groupEnd();
  }
  /**
   * Valide que l'URL de l'API est accessible
   */  async validateApiConnection(): Promise<boolean> {
    try {
      // Utiliser l'URL complète pour le test, en enlèvant "/api/v1" si présent
      const urlToCheck = this.apiUrl.replace(/\/api\/v1\/?$/, '');
      
      // Vérifier si l'URL contient déjà un protocole
      const hasProtocol = /^https?:\/\//i.test(urlToCheck);
      // Ajouter le protocole si manquant
      const fullUrl = hasProtocol ? urlToCheck : `http://${urlToCheck}`;
      
      // Utiliser l'endpoint de santé pour valider la connexion
      const healthUrl = `${fullUrl}/health`;
      
      if (this.config.DEBUG) {
        console.log(`🔍 Vérification API: ${healthUrl}`);
      }
      
      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: AbortSignal.timeout(30000), // Timeout augmenté à 30 secondes
      });
      
      const isHealthy = response.ok;
      
      if (this.config.DEBUG) {
        console.log(`🔍 Test de connexion API: ${isHealthy ? '✅ OK' : '❌ Échec'}`);
      }
      
      return isHealthy;
    } catch (error) {
      if (this.config.DEBUG) {
        console.error("❌ Erreur de connexion API:", error);
      }
      return false;
    }
  }
}

// Instance singleton
export const configService = new ConfigService();

// Export des constantes pour compatibilité
export const API_URL = configService.apiUrl;
export const IS_DEV = configService.isDevMode;
export const IS_DEBUG = configService.isDebugMode;

export default configService;
