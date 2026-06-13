import { toastManager } from "@/services/toastManager";

export type MessageHandler = (data: any) => void;

/**
 * Service WebSocket pour les connexions en temps réel
 * Se connecte à /api/ws/admin_ws.py
 */
export class WebSocketService {
  private socket: WebSocket | null = null;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private token: string | null = null;
  private lastHeartbeat: number = 0;
  private heartbeatInterval: number = 30000; // 30 secondes
  private heartbeatTimeout: NodeJS.Timeout | null = null;
  private messageSequence: Map<string, number> = new Map();

  /**
   * Initialise la connexion WebSocket
   * @param token Token JWT pour l'authentification
   */
  public connect(token: string): void {
    if (this.socket) {
      this.disconnect();
    }

    this.token = token;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Récupérer l'URL de base du backend depuis le localStorage ou les variables d'environnement
    // Si elle existe dans localStorage, elle a la priorité
    const savedApiUrl = localStorage.getItem('CREC_API_URL');
    // Extraire l'URL de base (sans le chemin api/v1)
    let apiBaseUrl;
    
    if (savedApiUrl) {
      // Si l'URL est enregistrée dans localStorage, l'utiliser
      apiBaseUrl = savedApiUrl.replace(/\/api\/v1\/?$/, '');
    } else if (import.meta.env.VITE_API_URL) {
      // Sinon, utiliser la variable d'environnement, en enlevant "/api/v1" s'il existe
      apiBaseUrl = import.meta.env.VITE_API_URL.replace(/\/api\/v1\/?$/, '');
    } else {
      // Par défaut, utiliser l'origine du site actuel
      apiBaseUrl = `${window.location.protocol}//${window.location.host}`;
    }
    
    // Construire l'URL WebSocket avec le bon protocole
    let wsBaseUrl;
    try {
      // Convertir en URL pour normaliser et extraire les parties
      const url = new URL(apiBaseUrl);
      wsBaseUrl = `${url.protocol === 'https:' ? 'wss:' : 'ws:'}`;
      
      // Ne pas ajouter le port s'il est standard (80 pour http, 443 pour https)
      const isStandardPort = (url.protocol === 'http:' && url.port === '80') || 
                           (url.protocol === 'https:' && url.port === '443') ||
                           url.port === '';
      
      // Construire l'URL en utilisant le hostname et en ajoutant le port uniquement s'il est non-standard
      wsBaseUrl += `//${url.hostname}${isStandardPort ? '' : `:${url.port}`}`;
    } catch (e) {
      // Fallback si l'URL n'est pas une URL valide
      console.warn("URL de l'API invalide, utilisation de l'URL de la page");
      wsBaseUrl = `${wsProtocol}//${window.location.host}`;
    }

    // Ajout du chemin spécifique pour les WebSockets et du canal 'all'
    const finalWsUrl = `${wsBaseUrl}/api/v1/ws/?channel=all&token=${token}`;
    
    console.log('🔌 Tentative de connexion WebSocket:', finalWsUrl);
    
    try {
      this.socket = new WebSocket(finalWsUrl);

      this.socket.onopen = () => {
        console.log('✅ WebSocket connection established');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket connection closed:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        this.isConnected = false;
        this.stopHeartbeat();
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.isConnected = false;
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          console.log('📩 Message WebSocket reçu:', message);
          
          // Gestion du heartbeat
          if (message.type === 'heartbeat') {
            this.lastHeartbeat = Date.now();
            return;
          }

          // Vérification de la séquence des messages
          if (message.sequence_id !== undefined) {
            const lastSequence = this.messageSequence.get(message.channel) || 0;
            if (message.sequence_id <= lastSequence) {
              console.warn(`Message séquentiel ignoré: ${message.sequence_id} <= ${lastSequence}`);
              return;
            }
            this.messageSequence.set(message.channel, message.sequence_id);
          }

          // Traitement des messages normaux
          if (message.channel && this.handlers.has(message.channel)) {
            console.log(`🎯 Handler trouvé pour channel: ${message.channel}`);
            const handlersSet = this.handlers.get(message.channel);
            if (handlersSet) {
              handlersSet.forEach((handler) => handler(message.data));
            }
          } else if (message.type && this.handlers.has(message.type)) {
            console.log(`🎯 Handler trouvé pour type: ${message.type}`);
            const handlersSet = this.handlers.get(message.type);
            if (handlersSet) {
              handlersSet.forEach((handler) => handler(message.data));
            }
          } else {
            console.warn('⚠️ Aucun handler trouvé pour le message:', {
              hasChannel: !!message.channel,
              channel: message.channel,
              hasType: !!message.type,
              type: message.type,
              availableHandlers: Array.from(this.handlers.keys())
            });
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  /**
   * Démarre le monitoring du heartbeat
   */
  private startHeartbeat(): void {
    this.lastHeartbeat = Date.now();
    this.heartbeatTimeout = setInterval(() => {
      const now = Date.now();
      if (now - this.lastHeartbeat > this.heartbeatInterval * 2) {
        console.warn('Heartbeat timeout - reconnecting...');
        this.disconnect();
        this.attemptReconnect();
      }
    }, this.heartbeatInterval);
  }

  /**
   * Arrête le monitoring du heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimeout) {
      clearInterval(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Tente de se reconnecter au WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }    if (this.reconnectAttempts < this.maxReconnectAttempts && this.token) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * (2 ** this.reconnectAttempts), 30000);
      
      // toastManager.warning(
      //   `Connexion perdue. Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`,
      //   { duration: delay }
      // );
      
      this.reconnectTimeout = setTimeout(() => {
        if (this.token) {
          this.connect(this.token);
        }
      }, delay);
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      toastManager.error('Impossible de rétablir la connexion. Veuillez rafraîchir la page.');
    }
  }

  /**
   * Ferme la connexion WebSocket
   */
  public disconnect(): void {
    this.stopHeartbeat();
    
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
      
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
    }
    this.token = null;
  }

  /**
   * Enregistre un gestionnaire pour un type de message spécifique
   * @param type Type de message à écouter
   * @param handler Fonction de traitement du message
   */
  public subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    
    this.handlers.get(type)?.add(handler);
    
    // Retourne une fonction pour se désabonner
    return () => {
      const handlersSet = this.handlers.get(type);
      if (handlersSet) {
        handlersSet.delete(handler);
        if (handlersSet.size === 0) {
          this.handlers.delete(type);
        }
      }
    };
  }
  /**
   * Envoie un message sur le WebSocket
   * @param type Type de message
   * @param data Données à envoyer
   */
  public send(type: string, data: any): void {
    if (!this.isConnected || !this.socket) {
      toastManager.error("Pas de connexion WebSocket établie");
      return;
    }
    
    try {
      this.socket.send(JSON.stringify({ type, data }));
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      toastManager.error("Erreur lors de l'envoi du message");
    }
  }

  /**
   * Vérifie si la connexion WebSocket est active
   */
  public getConnectionStatus(): boolean {
    return this.isConnected && this.socket !== null;
  }
}

// Instance singleton
export const websocketService = new WebSocketService();

export default websocketService;
