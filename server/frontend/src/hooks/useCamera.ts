import { useState, useEffect, useRef, useCallback } from 'react';

interface UseCameraOptions {
  defaultDeviceId?: string;
  constraints?: MediaStreamConstraints['video'];
  autoStart?: boolean;
}

interface UseCameraReturn {
  stream: MediaStream | null;
  isLoading: boolean;
  error: string;
  devices: MediaDeviceInfo[];
  selectedDevice: string;
  videoRef: React.RefObject<HTMLVideoElement>;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
  setSelectedDevice: (deviceId: string) => void;
  reconnectCamera: () => Promise<void>;
}

export const useCamera = (options: UseCameraOptions = {}): UseCameraReturn => {
  const {
    defaultDeviceId,
    constraints = {
      width: { ideal: 640, min: 480 },
      height: { ideal: 480, min: 360 },
      facingMode: 'user'
    },
    autoStart = false
  } = options;

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>(defaultDeviceId || "");
  const [devicesInitialized, setDevicesInitialized] = useState(false);
  
  // Références pour éviter les cycles infinis et les conditions de course
  const startingRef = useRef(false);
  const mountedRef = useRef(true);
  const videoRef = useRef<HTMLVideoElement>(null);
  const currentStreamRef = useRef<MediaStream | null>(null);
  const attemptTimeoutRef = useRef<number | null>(null);

  // Récupérer les appareils vidéo disponibles sans répétition inutile
  const getVideoDevices = useCallback(async () => {
    try {
      console.log("Récupération des appareils vidéo...");
      
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        throw new Error("API mediaDevices non disponible");
      }
      
      let deviceList: MediaDeviceInfo[];
      
      // Obtenir les permissions pour accéder aux labels
      try {
        const tempConstraints = { video: true, audio: false };
        const tempStream = await navigator.mediaDevices.getUserMedia(tempConstraints);
        tempStream.getTracks().forEach(track => track.stop());
        
        deviceList = await navigator.mediaDevices.enumerateDevices();
      } catch (err) {
        console.warn("Impossible d'obtenir les labels des appareils:", err);
        deviceList = await navigator.mediaDevices.enumerateDevices();
      }
      
      const videoDevices = deviceList.filter(device => device.kind === 'videoinput');
      console.log("Appareils vidéo disponibles:", videoDevices);
      
      if (!mountedRef.current) return videoDevices; // Éviter les mises à jour si démonté
      
      setDevices(videoDevices);
      
      // Ne définir selectedDevice que si nécessaire et une seule fois
      if (videoDevices.length > 0 && !selectedDevice && !devicesInitialized) {
        console.log("Sélection automatique du premier appareil:", videoDevices[0].deviceId);
        setSelectedDevice(videoDevices[0].deviceId);
      } else if (videoDevices.length === 0) {
        setError("Aucune caméra détectée sur cet appareil");
      }
      
      setDevicesInitialized(true);
      return videoDevices;
    } catch (err: any) {
      if (!mountedRef.current) return [];
      
      console.error("Erreur lors de l'énumération des appareils:", err);
      setError(`Impossible d'énumérer les appareils vidéo: ${err.message}`);
      return [];
    }
  }, [selectedDevice, devicesInitialized]);

  // Fonction sécurisée pour nettoyer un stream
  const cleanupStream = useCallback((streamToClean: MediaStream | null) => {
    if (streamToClean) {
      try {
        streamToClean.getTracks().forEach(track => {
          try {
            if (track.readyState === 'live') {
              track.stop();
            }
          } catch (err) {
            console.warn("Erreur lors de l'arrêt d'une piste:", err);
          }
        });
      } catch (err) {
        console.warn("Erreur lors du nettoyage du stream:", err);
      }
    }
  }, []);

  // Démarrer la caméra avec protection contre les démarrages multiples
  const startCamera = useCallback(async () => {
    // Protection contre les démarrages simultanés
    if (startingRef.current || !mountedRef.current) {
      console.log("Démarrage déjà en cours ou hook démonté, ignoré");
      return;
    }
    
    startingRef.current = true;
    setIsLoading(true);
    setError("");
    
    // Nettoyer tout précédent timeout
    if (attemptTimeoutRef.current) {
      clearTimeout(attemptTimeoutRef.current);
      attemptTimeoutRef.current = null;
    }
    
    try {
      console.log("Démarrage de la caméra...");
      
      // Arrêt propre du stream actuel
      cleanupStream(currentStreamRef.current);
      currentStreamRef.current = null;
      
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      
      // Vérifications de base
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("API getUserMedia non disponible");
      }
      
      if (!selectedDevice) {
        console.log("Aucun appareil sélectionné, tentative de récupération des appareils");
        const devices = await getVideoDevices();
        if (devices.length === 0) {
          throw new Error("Aucune caméra disponible");
        }
      }
      
      // Construction des contraintes
      const videoConstraints = {
        ...(typeof constraints === 'object' ? constraints : {}),
        deviceId: selectedDevice ? { exact: selectedDevice } : undefined
      };
      
      const mediaConstraints: MediaStreamConstraints = {
        video: videoConstraints,
        audio: false
      };
      
      console.log("Demande d'accès à la caméra avec contraintes:", JSON.stringify(mediaConstraints));
      
      // Obtention du flux vidéo
      const newStream = await navigator.mediaDevices.getUserMedia(mediaConstraints);
      
      // Vérifier si le hook est toujours monté
      if (!mountedRef.current) {
        cleanupStream(newStream);
        return;
      }
      
      // Stockage du flux
      currentStreamRef.current = newStream;
      setStream(newStream);
      
      if (videoRef.current && mountedRef.current) {
        // Attacher le flux à l'élément vidéo
        console.log("Attachement du flux vidéo à l'élément");
        videoRef.current.srcObject = newStream;
        
        // Démarrer la lecture avec une gestion résiliente des erreurs
        await new Promise<void>((resolve, reject) => {
          if (!videoRef.current || !mountedRef.current) {
            return reject(new Error("Élément vidéo non disponible"));
          }
          
          const video = videoRef.current;
          
          // Fonction de cleanup
          const cleanup = () => {
            video.removeEventListener('loadedmetadata', onLoadedMetadata);
            video.removeEventListener('loadeddata', onLoadedData);
            video.removeEventListener('canplay', onCanPlay);
            video.removeEventListener('error', onError);
            
            if (attemptTimeoutRef.current) {
              clearTimeout(attemptTimeoutRef.current);
              attemptTimeoutRef.current = null;
            }
          };
          
          // Événements pour détecter quand la vidéo est prête
          const onLoadedMetadata = () => {
            console.log("Événement loadedmetadata détecté");
            tryPlay();
          };
          
          const onLoadedData = () => {
            console.log("Événement loadeddata détecté");
            tryPlay();
          };
          
          const onCanPlay = () => {
            console.log("Événement canplay détecté");
            tryPlay();
          };
          
          // Gestion des erreurs
          const onError = (e: Event) => {
            console.error("Erreur de l'élément vidéo:", e);
            cleanup();
            reject(new Error("Erreur lors du chargement de la vidéo"));
          };
          
          // Essai de lecture
          const tryPlay = async () => {
            try {
              // Si la lecture est déjà en cours ou terminée, ne rien faire
              if (video.paused === false) {
                console.log("La vidéo est déjà en lecture");
                cleanup();
                resolve();
                return;
              }
              
              await video.play();
              console.log("Lecture vidéo démarrée avec succès");
              cleanup();
              resolve();
            } catch (err) {
              console.warn("Échec du démarrage de la lecture, nouvelle tentative programmée:", err);
              // Ne pas nettoyer ici, on va réessayer
            }
          };
          
          // Attacher les événements
          video.addEventListener('loadedmetadata', onLoadedMetadata);
          video.addEventListener('loadeddata', onLoadedData);
          video.addEventListener('canplay', onCanPlay);
          video.addEventListener('error', onError);
          
          // Timeout de sécurité avec réessais
          let attempts = 0;
          const maxAttempts = 5;
          
          const scheduleAttempt = () => {
            if (!mountedRef.current) return;
            
            attempts++;
            if (attempts > maxAttempts) {
              console.error("Nombre maximum de tentatives atteint");
              cleanup();
              reject(new Error("Impossible de démarrer la lecture après plusieurs tentatives"));
              return;
            }
            
            // Délai exponentiel pour les tentatives
            const delay = Math.min(100 * Math.pow(2, attempts), 3000);
            console.log(`Programmation de la tentative ${attempts}/${maxAttempts} dans ${delay}ms`);
            
            attemptTimeoutRef.current = window.setTimeout(() => {
              if (!mountedRef.current) return;
              
              tryPlay().catch(() => {
                scheduleAttempt();
              });
            }, delay);
          };
          
          // Première tentative immédiate
          tryPlay().catch(() => {
            scheduleAttempt();
          });
        });
      }
      
      console.log("Caméra initialisée avec succès");
    } catch (err: any) {
      if (!mountedRef.current) return;
      
      console.error("Erreur lors de l'initialisation de la caméra:", err);
      
      // Nettoyer le stream en cas d'échec
      cleanupStream(currentStreamRef.current);
      currentStreamRef.current = null;
      setStream(null);
      
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      
      // Message d'erreur approprié
      let errorMessage = "Impossible d'accéder à la caméra";
      
      switch(err.name) {
        case 'NotAllowedError':
          errorMessage = "L'autorisation d'accès à la caméra a été refusée";
          break;
        case 'NotFoundError':
          errorMessage = "Aucune caméra n'est disponible sur cet appareil";
          break;
        case 'NotReadableError':
          errorMessage = "La caméra est utilisée par une autre application";
          break;
        case 'OverconstrainedError':
          errorMessage = "Les paramètres demandés ne sont pas supportés par cette caméra";
          break;
        case 'AbortError':
          errorMessage = "L'initialisation de la caméra a été interrompue";
          break;
      }
      
      setError(`${errorMessage} (${err.name || 'Error'}: ${err.message})`);
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
      startingRef.current = false;
    }
  }, [selectedDevice, constraints, getVideoDevices, cleanupStream]);

  // Arrêter proprement la caméra
  const stopCamera = useCallback(() => {
    console.log("Arrêt de la caméra");
    
    // Nettoyer les timeouts
    if (attemptTimeoutRef.current) {
      clearTimeout(attemptTimeoutRef.current);
      attemptTimeoutRef.current = null;
    }
    
    // Arrêter le stream
    cleanupStream(currentStreamRef.current);
    currentStreamRef.current = null;
    
    if (mountedRef.current) {
      setStream(null);
    }
    
    // Nettoyer l'élément vidéo
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, [cleanupStream]);

  // Reconnecter la caméra
  const reconnectCamera = useCallback(async () => {
    console.log("Reconnexion de la caméra...");
    stopCamera();
    
    // Attendre un peu avant de redémarrer
    await new Promise(resolve => setTimeout(resolve, 300));
    
    if (mountedRef.current) {
      await startCamera();
    }
  }, [stopCamera, startCamera]);

  // Changer de dispositif
  const handleSetSelectedDevice = useCallback((deviceId: string) => {
    if (deviceId !== selectedDevice) {
      console.log(`Changement de dispositif: ${deviceId}`);
      setSelectedDevice(deviceId);
    }
  }, [selectedDevice]);

  // Initialisation - récupérer les appareils au chargement
  useEffect(() => {
    console.log("Initialisation du hook useCamera");
    mountedRef.current = true;
    
    getVideoDevices();
    
    // Surveiller les changements de périphériques
    const handleDeviceChange = () => {
      console.log("Changement de périphériques détecté");
      if (mountedRef.current) {
        getVideoDevices();
      }
    };
    
    try {
      navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange);
    } catch (err) {
      console.warn("Impossible de surveiller les changements de périphériques:", err);
    }
    
    return () => {
      console.log("Nettoyage du hook useCamera");
      mountedRef.current = false;
      
      try {
        navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange);
      } catch (err) {
        console.warn("Erreur lors du nettoyage des écouteurs d'événements:", err);
      }
      
      // Nettoyer les timeouts
      if (attemptTimeoutRef.current) {
        clearTimeout(attemptTimeoutRef.current);
        attemptTimeoutRef.current = null;
      }
      
      // Arrêter proprement la caméra
      cleanupStream(currentStreamRef.current);
      currentStreamRef.current = null;
    };
  }, [getVideoDevices, cleanupStream]);

  // Démarrage automatique
  useEffect(() => {
    // Démarrer seulement si on a un appareil sélectionné et que l'initialisation est complète
    if (selectedDevice && devicesInitialized && !isLoading && !stream && !startingRef.current && mountedRef.current) {
      // Attendre un peu pour éviter les démarrages trop rapprochés
      const timer = setTimeout(() => {
        if (mountedRef.current && !stream && !startingRef.current) {
          startCamera();
        }
      }, 300);
      
      return () => clearTimeout(timer);
    }
  }, [selectedDevice, devicesInitialized, isLoading, stream, startCamera]);

  return {
    stream,
    isLoading,
    error,
    devices,
    selectedDevice,
    videoRef,
    startCamera,
    stopCamera,
    setSelectedDevice: handleSetSelectedDevice,
    reconnectCamera,
  };
};
