import React, { useState, useRef, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowLeft,
  ArrowRight,
  Camera,
  UserPlus,
  RotateCcw,
  Save,
  Trash2,
  ChevronLeft,
  Video,
  HelpCircle,
} from "lucide-react";
import { useStudents } from "@/hooks/useStudents";
import { useCamera } from "@/hooks/useCamera";
import { StudentRead } from "@/types/studentTypes";
import KeyboardShortcutsHelp from "@/components/enrollment/KeyboardShortcutsHelp";
import WelcomeGuide from "@/components/enrollment/WelcomeGuide";
import StudentInfoPanel from "@/components/enrollment/StudentInfoPanel";
import AddStudentWithEnrollment from "@/components/enrollment/AddStudentWithEnrollment";

// Import du service d'enrôlement facial
import { faceEnrollmentApi } from "@/services/api/faceEnrollment";
import { StudentBase } from "@/types/studentTypes";
import { useSettings } from "@/hooks/useSettings";


interface CapturedPhoto {
  id: number;
  blob: Blob;
  url: string;
  timestamp: Date;
}

const FaceEnrollment = () => {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // États pour la gestion des apprenants
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [selectedClass, setSelectedClass] = useState<string>("all");
  const [currentStudentIndex, setCurrentStudentIndex] = useState(0);
  // États pour la capture vidéo (utilise le hook useCamera)
  const {
    stream,
    isLoading: isCameraLoading,
    error: cameraError,
    devices,
    selectedDevice,
    videoRef,
    stopCamera,
    setSelectedDevice,
    reconnectCamera,
  } = useCamera({ autoStart: false });
  
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedPhotos, setCapturedPhotos] = useState<CapturedPhoto[]>([]);

  // État pour l'aide des raccourcis clavier
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);
  const [showWelcomeGuide, setShowWelcomeGuide] = useState(true);
  
  // État pour la soumission
  const [isSubmitting, setIsSubmitting] = useState(false);// Récupération des données des apprenants
  const {
    studentsPage,
    isLoading,
    update,
    create,
  } = useStudents();
    // Récupération des paramètres système pour la promotion
  const { settings } = useSettings();
  const promotion = settings?.system?.current_promotion || "2024-2025";
  
  const students = studentsPage?.items || [];
  const totalStudents = students.length;
  
  // Filtrer d'abord les étudiants dont le visage n'est pas enrôlé
  const unenrolledStudents = students.filter(s => !s.faceEnrolled);
  const totalUnenrolledStudents = unenrolledStudents.length;
  
  // Filtrer les étudiants non-enrôlés par classe sélectionnée
  const filteredStudents = selectedClass === "all" ? unenrolledStudents : unenrolledStudents.filter(s => s.classGroup === selectedClass);
    const currentStudent = filteredStudents.find(s => s.id === selectedStudentId);
    // Obtenir toutes les classes disponibles (de tous les étudiants, pas seulement les non-enrôlés)
  const availableClasses = React.useMemo(() => {
    const classes = [...new Set(students.map(s => s.classGroup).filter(Boolean))];
    return classes.sort();
  }, [students]);  // Variables calculées
  const progressPercentage = Math.round((capturedPhotos.length / 6) * 100);
  const canSave = capturedPhotos.length === 6;

  // Capturer une photo
  const capturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    setIsCapturing(true);

    // Petit délai pour le feedback visuel
    await new Promise(resolve => setTimeout(resolve, 500));

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    if (!context) {
      setIsCapturing(false);
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (blob) {
        const newPhoto: CapturedPhoto = {
          id: Date.now(),
          blob,
          url: URL.createObjectURL(blob),
          timestamp: new Date(),
        };

        setCapturedPhotos(prev => [...prev, newPhoto]);
        // Success notification would go here
        // console.log("Photo captured successfully");
      }
      setIsCapturing(false);
    }, 'image/jpeg', 0.9);
  };

  // Helper functions for notifications
  const showError = (message: string, options?: { title?: string }) => {
    console.error(options?.title || "Error", message);
  };

  const success = (message: string, options?: { title?: string }) => {
    console.log(options?.title || "Success", message);
  };

  // Supprimer une photo
  const removePhoto = (photoId: number) => {
    setCapturedPhotos(prev => {
      const photoToRemove = prev.find(p => p.id === photoId);
      if (photoToRemove) {
        URL.revokeObjectURL(photoToRemove.url);
      }
      return prev.filter(p => p.id !== photoId);
    });
  };

  // Effacer la dernière photo prise 
  const clearLastPhoto =  () => {
    if (capturedPhotos.length === 0) return;
    const lastPhoto = capturedPhotos[capturedPhotos.length - 1];
    removePhoto(lastPhoto.id);
  };

  // Effacer toutes les photos
  const clearAllPhotos = () => {
    capturedPhotos.forEach(photo => URL.revokeObjectURL(photo.url));
    setCapturedPhotos([]);
  };
  // Charger les données de l'apprenant sélectionné
  useEffect(() => {
    if (selectedStudentId) {
      const index = filteredStudents.findIndex(s => s.id === selectedStudentId);
      setCurrentStudentIndex(index);
    }
  }, [selectedStudentId, filteredStudents]);

  // Sélectionner automatiquement le premier apprenant disponible quand le filtre change
  useEffect(() => {
    if (filteredStudents.length > 0 && (!selectedStudentId || !filteredStudents.find(s => s.id === selectedStudentId))) {
      setSelectedStudentId(filteredStudents[0].id!);
    } else if (filteredStudents.length === 0) {
      setSelectedStudentId("");
    }
  }, [filteredStudents, selectedStudentId]);

  // Navigation entre apprenants
  const goToPreviousStudent = () => {
    const currentIndex = filteredStudents.findIndex(s => s.id === selectedStudentId);
    if (currentIndex > 0) {
      const prevStudent = filteredStudents[currentIndex - 1];
      setSelectedStudentId(prevStudent.id!);
      clearAllPhotos();
    }
  };

  const goToNextStudent = () => {
    const currentIndex = filteredStudents.findIndex(s => s.id === selectedStudentId);
    if (currentIndex < filteredStudents.length - 1) {
      const nextStudent = filteredStudents[currentIndex + 1];
      setSelectedStudentId(nextStudent.id!);
      clearAllPhotos();
    }
  };
  // Mettre à jour les informations de l'apprenant
  const handleUpdateStudentInfo = async (data: Partial<any>) => {
    if (!selectedStudentId) return;
    
    try {
      await update.mutateAsync({
        id: selectedStudentId,
        data
      });
      success("Informations mises à jour avec succès", { title: "Modification sauvegardée" });
    } catch (error) {
      showError("Impossible de mettre à jour les informations", { title: "Erreur de sauvegarde" });
      throw error;
    }
  };
  // Ajouter un nouvel apprenant depuis la page d'enrôlement
  const handleAddNewStudent = async (studentData: StudentBase) => {
    try {
      const result = await create.mutateAsync(studentData);
      
      if (result.success) {
        // Sélectionner automatiquement le nouvel apprenant créé par son ID
        if (studentData.id) {
          setSelectedStudentId(studentData.id);
          // Réinitialiser les photos en cas de changement d'apprenant
          clearAllPhotos();
          success(
            `${studentData.firstName} ${studentData.lastName} a été créé et sélectionné pour l'enrôlement !`,
            { title: "Apprenant créé" }
          );
        }
      } else {
        throw new Error(result.message || "Échec de la création de l'apprenant");
      }
    } catch (error: any) {
      const errorMessage = error.message || "Impossible de créer l'apprenant";
      showError(errorMessage, { title: "Erreur de création" });
      throw error;
    }
  };

  // Sauvegarder l'enrôlement
  const saveEnrollment = async () => {
    if (!selectedStudentId || capturedPhotos.length < 6) {
      showError("6 photos sont requises pour l'enrôlement", { title: "Photos manquantes" });
      return;
    }

    const studentName = currentStudent ? `${currentStudent.firstName} ${currentStudent.lastName}` : "Apprenant";
    setIsSubmitting(true);

    try {
      // Extraire les blobs des photos capturées
      const photoBlobs = capturedPhotos.map(photo => photo.blob);
      
      // Upload et traitement des photos
      const result = await faceEnrollmentApi.uploadEnrollmentPhotos(selectedStudentId, photoBlobs);
      
      if (result) {
        // Marquer l'étudiant comme ayant un visage enrôlé
        await handleUpdateStudentInfo({ faceEnrolled: true });
        
        success(
          `Enrôlement de ${studentName} terminé avec succès ! `,
          { title: "Enrôlement réussi" }
        );
        
        // Suppression des photos capturées
        clearAllPhotos();

        // Passer à l'apprenant suivant automatiquement
        const currentIndex = filteredStudents.findIndex(s => s.id === selectedStudentId);
        if (currentIndex < filteredStudents.length - 1) {
          goToNextStudent();
        } else {
          // Si c'était le dernier apprenant, réinitialiser la sélection
          setSelectedStudentId("");
        }
      } else {
        showError("L'enrôlement n'a pas pu être finalisé", { title: "Erreur d'enrôlement" });
        return;
      }
    } catch (error: any) {
      console.error("Erreur lors de l'enrôlement:", error);
      const errorMessage = error.message || "Impossible de sauvegarder l'enrôlement";
      showError(errorMessage, { title: "Erreur de sauvegarde" });
    } finally {    setIsSubmitting(false);
    }
  };

  // Raccourcis clavier pour une meilleure UX
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // Vérifier si l'utilisateur est en train de taper dans un champ de saisie
      const target = event.target as HTMLElement;
      const isInputFocused = target && (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.contentEditable === 'true' ||
        target.closest('[role="combobox"]') || // Pour les Select de shadcn/ui
        target.closest('[data-radix-select-trigger]') || // Pour les Select Radix
        target.closest('[data-radix-collection-item]') // Pour les options de Select
      );

      // Si l'utilisateur tape dans un champ, on ignore tous les raccourcis sauf F1
      if (isInputFocused && event.code !== 'F1') {
        return; // Laisser le comportement normal du navigateur
      }

      // F1 pour ouvrir l'aide (toujours disponible)
      if (event.code === 'F1') {
        event.preventDefault();
        setShowKeyboardHelp(true);
        return;
      }

      // Pour les autres raccourcis, empêcher le comportement par défaut
      // seulement si on n'est pas dans un champ de saisie
      
      // Espace pour capturer
      if (event.code === 'Space' && stream && capturedPhotos.length < 6 && !isCapturing) {
        event.preventDefault();
        capturePhoto();
      }

      // Backspace pour effacer la dernière photo
      if (event.code === 'Backspace' && capturedPhotos.length > 0) {
        event.preventDefault();
        clearLastPhoto();
      }
      
      // Entrée pour sauvegarder
      if (event.code === 'Enter' && canSave) {
        event.preventDefault();
        saveEnrollment();
      }

      // Flèches pour navigation entre apprenants
      const currentIndex = filteredStudents.findIndex(s => s.id === selectedStudentId);
      if (event.code === 'ArrowLeft' && currentIndex > 0) {
        event.preventDefault();
        goToPreviousStudent();
      }
      if (event.code === 'ArrowRight' && currentIndex < filteredStudents.length - 1) {
        event.preventDefault();
        goToNextStudent();
      }
    };    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [stream, capturedPhotos.length, isCapturing, canSave, selectedStudentId, filteredStudents]);

  // Nettoyage au démontage du composant
  useEffect(() => {
    return () => {
      capturedPhotos.forEach(photo => URL.revokeObjectURL(photo.url));
    };
  }, [capturedPhotos]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="p-4 text-center">Chargement des apprenants...</div>
      </MainLayout>
    );
  }  return (
    <MainLayout requiredRoles={["admin", "pedagogical"]} forceSidebarClosed={true}>
      <div className="space-y-4 lg:space-y-6 p-4 sm:p-6 lg:p-8">
        {/* Breadcrumb et header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/apprenants')}
              className="p-0 h-auto text-blue-600 hover:text-blue-800"
            >
              Gestion des Apprenants
            </Button>            
            <span>&gt;</span>            
            <span className="font-medium">Enrôlement des visages</span>
            {currentStudent && (
              <>
                <span>&gt;</span>
                <span className="font-medium text-blue-600">Apprenant {currentStudent.id}</span>
              </>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowKeyboardHelp(true)}
              className="text-gray-500 hover:text-gray-700"
              title="Aide - Raccourcis clavier (F1)"
            >
              <HelpCircle className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/apprenants')}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
          </div>
        </div>            {/* Navigation des apprenants avec filtre de classe */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex flex-col">
                <span className="text-lg lg:text-xl">Sélection de l'apprenant</span>
                <p className="text-sm font-normal text-gray-600 mt-1">
                  Seuls les apprenants sans enrôlement facial sont affichés
                </p>
              </div>
              {filteredStudents.length > 0 && selectedStudentId && (
                <Badge variant="outline" className="self-start lg:self-center">
                  Apprenant {currentStudentIndex + 1} sur {filteredStudents.length} (non-enrôlés)
                  {selectedClass !== "all" && ` (Classe: ${selectedClass})`}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 lg:px-6">
            <div className="space-y-4">
              {/* Filtre par classe - Responsive */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4"><div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-700 hidden sm:inline">Filtrer par classe:</span>
                  <span className="text-sm font-medium text-gray-700 sm:hidden">Classe:</span>
                </div>
                <div className="flex-1">
                  <Select value={selectedClass} onValueChange={setSelectedClass}>
                    <SelectTrigger className="w-full sm:w-64">
                      <SelectValue placeholder="Toutes les classes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Toutes les classes ({totalUnenrolledStudents} apprenants non-enrôlés)</SelectItem>
                      {availableClasses.map((className) => {
                        const count = unenrolledStudents.filter(s => s.classGroup === className).length;
                        return (
                          <SelectItem key={className} value={className}>
                            {className} ({count} apprenants non-enrôlés)
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
              </div>
                {/* Sélection de l'apprenant - Responsive */}
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Select value={selectedStudentId} onValueChange={setSelectedStudentId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Sélectionner un apprenant" />
                    </SelectTrigger>
                    <SelectContent>
                      {filteredStudents.map((student) => (
                        <SelectItem key={student.id} value={student.id!}>
                          <span className="truncate">
                            {student.id} - {student.firstName} {student.lastName} ({student.classGroup})
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex flex-wrap gap-2 sm:gap-2 justify-center sm:justify-start">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToPreviousStudent}
                    disabled={currentStudentIndex <= 0}
                    className="flex-1 sm:flex-none min-w-0"
                  >
                    <ArrowLeft className="h-4 w-4 mr-1" />
                    <span className="hidden sm:inline">Précédent</span>
                    <span className="sm:hidden">Préc.</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToNextStudent}
                    disabled={currentStudentIndex >= filteredStudents.length - 1}
                    className="flex-1 sm:flex-none min-w-0"
                  >
                    <span className="hidden sm:inline">Suivant</span>
                    <span className="sm:hidden">Suiv.</span>
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </Button>
                  
                  {/* Bouton pour ajouter un nouvel apprenant */}
                  <AddStudentWithEnrollment
                    onAddStudent={handleAddNewStudent}
                    classGroups={availableClasses}
                    promotion={promotion}
                  >
                    <Button
                      variant="default"
                      size="sm"
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <UserPlus className="h-4 w-4 mr-1" />
                      Nouvel apprenant
                    </Button>
                  </AddStudentWithEnrollment>
                </div>
              </div>
            </div>          
            </CardContent>
        </Card>        
        {/* Message si aucun apprenant non-enrôlé */}
        {totalUnenrolledStudents === 0 && (
          <Card>
            <CardContent className="text-center py-12">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Tous les apprenants sont enrôlés !</h3>
                  <p className="text-gray-600 mt-2">
                    Tous les apprenants de la base de données ont déjà un enrôlement facial.
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Total des apprenants dans le système : {totalStudents}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Message si aucun apprenant dans la classe sélectionnée */}
        {totalUnenrolledStudents > 0 && filteredStudents.length === 0 && selectedClass !== "all" && (
          <Card>
            <CardContent className="text-center py-12">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.232 18.5C3.462 20.333 4.424 22 5.982 22z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Aucun apprenant à enrôler dans cette classe</h3>
                  <p className="text-gray-600 mt-2">
                    Tous les apprenants de la classe "{selectedClass}" ont déjà un enrôlement facial.
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Apprenants non-enrôlés dans d'autres classes : {totalUnenrolledStudents}
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedClass("all")}
                    className="mt-4"
                  >
                    Voir toutes les classes
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        
        {selectedStudentId && (
          <>
            {/* Section centrale - Captures */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">                  
                  <span>Captures obligatoires (6 prises)</span>
                  <Badge 
                    variant={capturedPhotos.length === 6 ? "default" : "secondary"}
                    className={capturedPhotos.length === 6 ? "bg-green-500" : ""}
                  >
                    {capturedPhotos.length}/6 photos capturées
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">               
                 {/* Sélecteur de source vidéo */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                    <div className="flex items-center space-x-2">
                      <Video className="h-5 w-5 text-blue-600" />
                      <span className="font-medium">Source vidéo:</span>
                    </div>
                    <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                      <SelectTrigger className="w-full sm:w-64">
                        <SelectValue placeholder="Choisir une caméra" />
                      </SelectTrigger>
                      <SelectContent>
                        {devices.map((device) => (
                          <SelectItem key={device.deviceId} value={device.deviceId}>
                            {device.label || `Caméra ${device.deviceId.slice(0, 8)}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {/* Indicateur d'état et contrôles */}
                  <div className="flex items-center space-x-2">
                    {stream && !cameraError && !isCameraLoading && (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        🟢 Connecté
                      </Badge>
                    )}
                    {cameraError && !isCameraLoading && (
                      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                        🔴 Erreur
                      </Badge>
                    )}
                    {isCameraLoading && (
                      <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                        🟡 Connexion...
                      </Badge>
                    )}
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={reconnectCamera}
                      disabled={isCameraLoading}
                      className="text-blue-600 border-blue-200"
                    >
                      <RotateCcw className="h-4 w-4 mr-1" />
                      Reconnecter
                    </Button>
                  </div>
                </div>                  {/* Layout principal avec prévisualisation et informations étudiant */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 lg:gap-6">
                  {/* Prévisualisation vidéo - Responsive */}
                  <div className="flex flex-col order-2 xl:order-1">
                    <div className="flex justify-center">
                      <div className="relative w-full max-w-lg xl:max-w-none">
                        {/* Conteneur vidéo avec états - Responsive height */}
                        <div className="w-full h-64 sm:h-80 lg:h-96 bg-gray-900 rounded-lg border-2 sm:border-4 border-blue-200 relative overflow-hidden">
                          {/* Vidéo */}
                          <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className={`w-full h-full object-cover ${(!stream || isCameraLoading) ? 'hidden' : 'block'}`}
                          />
                          
                          {/* État de chargement */}
                          {isCameraLoading && (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                              <div className="text-center text-white">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                                <p>Initialisation de la caméra...</p>
                              </div>
                            </div>
                          )}
                          
                          {/* État d'erreur */}
                          {cameraError && !isCameraLoading && (
                            <div className="absolute inset-0 flex items-center justify-center bg-red-900">
                              <div className="text-center text-white p-4">
                                <Camera className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p className="text-sm mb-4">{cameraError}</p>                                <Button
                                  onClick={reconnectCamera}
                                  variant="outline"
                                  className="text-white border-white hover:bg-white hover:text-red-900"
                                >
                                  Réessayer
                                </Button>
                              </div>
                            </div>
                          )}
                          
                          {/* État par défaut (pas de caméra) */}
                          {!stream && !isCameraLoading && !cameraError && (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-700">
                              <div className="text-center text-gray-300">
                                <Camera className="h-12 w-12 mx-auto mb-4" />
                                <p>Caméra non active</p>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <canvas ref={canvasRef} className="hidden" />
                        
                        {/* Overlay pour guide de positionnement (seulement quand la vidéo est active) */}                        {stream && !isCameraLoading && !cameraError && (
                          <div className="absolute inset-0 pointer-events-none">
                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                              <div className="w-48 h-64 border-2 border-white border-dashed rounded-lg opacity-30"></div>
                            </div>
                          </div>
                        )}                          
                        {/* Bouton de capture - N'apparaît que s'il reste des photos à prendre */}
                        {capturedPhotos.length < 6 && (
                          <div className="mt-3 sm:mt-4 flex justify-center px-2 sm:px-0">
                            <Button
                              onClick={capturePhoto}
                              disabled={!stream || isCapturing || isCameraLoading || !!cameraError}
                              className="bg-blue-600 hover:bg-blue-700 px-4 sm:px-8 py-2 sm:py-3 text-base sm:text-lg disabled:opacity-50 w-full sm:w-auto max-w-xs"
                              size="lg"
                            >
                              <Camera className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                              <span className="truncate">
                                {isCapturing ? "Capture..." : `Capturer (${capturedPhotos.length + 1}/6)`}
                              </span>
                            </Button>
                          </div>
                        )}

                        {/* Statut de la caméra */}
                        {!stream && (
                          <div className="absolute inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center rounded-lg">
                            <div className="text-center text-white">
                              <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
                              <p className="text-sm">Caméra non disponible</p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>                        
                  {/* Panneau d'informations étudiant - Responsive order */}
                  <div className="flex flex-col order-1 xl:order-2">
                    {currentStudent && currentStudent.id && (
                      <StudentInfoPanel
                        student={{
                          id: currentStudent.id,
                          firstName: currentStudent.firstName,
                          lastName: currentStudent.lastName,
                          rfidUid: currentStudent.rfidUid,
                          classGroup: currentStudent.classGroup,
                          faceEnrolled: currentStudent.faceEnrolled
                        }}
                        onUpdateStudent={handleUpdateStudentInfo}
                        isLoading={false}
                        classGroups={availableClasses}
                      />
                    )}
                  </div>
                </div>                
                {/* Ultra-Premium Face Capture Interface */}
                <div className="mt-6 lg:mt-8 relative">
                  {/* Background Effects */}
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-pink-500/10 rounded-3xl blur-3xl -z-10"></div>
                  
                  <div className="flex flex-col lg:flex-row gap-4 lg:gap-8">
                    {/* Premium Photo Gallery - Responsive width */}
                    <div className="w-full lg:w-[50%] relative group">
                      {/* Glassmorphism Container */}
                      <div className="relative bg-white/40 backdrop-blur-xl border border-white/30 rounded-3xl p-6 shadow-2xl shadow-indigo-500/10 hover:shadow-3xl hover:shadow-indigo-500/20 transition-all duration-500">
                        {/* Header with Premium Badge */}
                        <div className="flex items-center justify-between mb-6">
                          <div className="flex items-center space-x-3">
                            <div className="relative">
                              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                                <Camera className="h-5 w-5 text-white" />
                              </div>
                              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full border-2 border-white animate-pulse"></div>
                            </div>
                            <div>
                              <h5 className="font-bold text-slate-800 text-base bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                Capture
                              </h5>
                            </div>
                          </div>
                          
                          {/* Premium Progress Badge */}
                          <div className="relative">
                            <div className={`px-4 py-2 rounded-2xl font-bold text-sm shadow-lg backdrop-blur-sm transition-all duration-300 ${
                              capturedPhotos.length === 6 
                                ? "bg-gradient-to-r from-emerald-400 to-green-500 text-white shadow-emerald-500/30" 
                                : "bg-white/60 text-slate-700 border border-white/50"
                            }`}>
                              <span className="font-mono">{capturedPhotos.length}</span>
                              <span className="mx-1 opacity-60">/</span>
                              <span className="font-mono">6</span>
                            </div>
                            {capturedPhotos.length === 6 && (
                              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-green-500 rounded-2xl blur-xl opacity-50 animate-pulse"></div>
                            )}
                          </div>
                        </div>
                          {/* Ultra-Modern Photo Grid - Responsive */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-4">
                          {[1, 2, 3, 4, 5, 6].map((index) => {
                            const photo = capturedPhotos[index - 1];
                            const isNext = index === capturedPhotos.length + 1;
                            const isCompleted = !!photo;
                            
                            return (
                              <div
                                key={index}
                                className={`aspect-[3/4] relative rounded-2xl overflow-hidden transition-all duration-500 transform hover:scale-105 hover:-translate-y-1 ${
                                  isCompleted
                                    ? "shadow-2xl shadow-emerald-500/20 ring-2 ring-emerald-400/50" 
                                    : isNext
                                    ? "shadow-xl shadow-indigo-500/20 ring-2 ring-indigo-400/50 animate-pulse" 
                                    : "shadow-lg shadow-slate-200/50 ring-1 ring-slate-200/50"
                                }`}
                                style={{ maxHeight: '160px' }}
                              >
                                {photo ? (
                                  <>
                                    {/* Photo with Premium Overlay */}
                                    <div className="relative w-full h-full">
                                      <img
                                        src={photo.url}
                                        alt={`Capture ${index}`}
                                        className="w-full h-full object-cover"
                                      />
                                      
                                      {/* Gradient Overlay */}
                                      <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent"></div>
                                      
                                      {/* Success Badge */}
                                      <div className="absolute top-2 left-2">
                                        <div className="w-6 h-6 bg-gradient-to-br from-emerald-400 to-green-500 rounded-full flex items-center justify-center shadow-lg">
                                          <span className="text-white text-xs font-bold">✓</span>
                                        </div>
                                      </div>
                                      
                                      {/* Photo Number */}
                                      <div className="absolute bottom-2 left-2">
                                        <div className="px-2 py-1 bg-black/60 backdrop-blur-sm rounded-lg">
                                          <span className="text-white text-xs font-bold">#{index}</span>
                                        </div>
                                      </div>
                                      
                                      {/* Delete Button */}
                                      <div className="absolute top-2 right-2">
                                        <Button
                                          variant="destructive"
                                          size="sm"
                                          onClick={() => removePhoto(photo.id)}
                                          className="h-6 w-6 p-0 rounded-full bg-red-500/90 hover:bg-red-600 backdrop-blur-sm shadow-lg border border-white/20"
                                        >
                                          <Trash2 className="h-3 w-3" />
                                        </Button>
                                      </div>
                                    </div>
                                  </>
                                ) : (
                                  <>
                                    {/* Empty Slot with Modern Design */}
                                    <div className={`w-full h-full flex flex-col items-center justify-center relative ${
                                      isNext 
                                        ? "bg-gradient-to-br from-indigo-50 to-purple-50" 
                                        : "bg-gradient-to-br from-slate-50 to-slate-100"
                                    }`}>
                                      
                                      {/* Background Pattern */}
                                      <div className="absolute inset-0 opacity-10">
                                        <div className="w-full h-full bg-gradient-to-br from-transparent via-white to-transparent"></div>
                                      </div>
                                      
                                      {/* Icon */}
                                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-2 shadow-lg transition-all duration-300 ${
                                        isNext 
                                          ? "bg-gradient-to-br from-indigo-400 to-purple-500 animate-pulse" 
                                          : "bg-gradient-to-br from-slate-300 to-slate-400"
                                      }`}>
                                        <Camera className={`h-6 w-6 text-white`} />
                                      </div>
                                      
                                      {/* Label */}
                                      <span className={`text-sm font-bold ${
                                        isNext ? "text-indigo-600" : "text-slate-500"
                                      }`}>
                                        {isNext ? "Suivante" : `#${index}`}
                                      </span>
                                      
                                      {isNext && (
                                        <div className="mt-1 text-xs text-indigo-500 font-medium animate-pulse">
                                          En attente...
                                        </div>
                                      )}
                                    </div>
                                  </>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>                    
                    {/* Premium Control Panel - Responsive width */}
                    <div className="w-full lg:w-[50%] space-y-4 lg:space-y-6">
                      {/* Circular Progress Dashboard */}
                      <div className="relative bg-white/40 backdrop-blur-xl border border-white/30 rounded-3xl p-6 shadow-2xl shadow-purple-500/10">
                        <div className="text-center">
                          <h5 className="font-bold text-slate-800 mb-6 text-lg bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                            Progression de l'Enrôlement
                          </h5>
                          
                          {/* Circular Progress */}
                          <div className="relative flex items-center justify-center mb-6">
                            <div className="relative w-32 h-32">
                              {/* Background Circle */}
                              <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
                                <circle
                                  cx="60"
                                  cy="60"
                                  r="50"
                                  stroke="currentColor"
                                  strokeWidth="8"
                                  fill="none"
                                  className="text-slate-200"
                                />
                                {/* Progress Circle */}
                                <circle
                                  cx="60"
                                  cy="60"
                                  r="50"
                                  stroke="url(#gradient)"
                                  strokeWidth="8"
                                  fill="none"
                                  strokeLinecap="round"
                                  strokeDasharray={`${(progressPercentage * 314) / 100} 314`}
                                  className="transition-all duration-700 ease-out drop-shadow-lg"
                                />
                                <defs>
                                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="#8b5cf6" />
                                    <stop offset="50%" stopColor="#a855f7" />
                                    <stop offset="100%" stopColor="#ec4899" />
                                  </linearGradient>
                                </defs>
                              </svg>
                              
                              {/* Center Content */}
                              <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <div className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                                  {progressPercentage}%
                                </div>
                                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                  Complété
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Status Badge */}
                          <div className="flex justify-center mb-4">
                            <div className={`px-6 py-3 rounded-2xl font-bold text-sm shadow-lg transition-all duration-300 ${
                              canSave 
                                ? "bg-gradient-to-r from-emerald-400 to-green-500 text-white shadow-emerald-500/30" 
                                : "bg-white/60 text-slate-700 border border-white/50"
                            }`}>
                              {canSave ? (
                                <div className="flex items-center space-x-2">
                                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                                  <span>Prêt à Valider</span>
                                </div>
                              ) : (
                                <div className="flex items-center space-x-2">
                                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse"></div>
                                  <span>{6 - capturedPhotos.length} photos restantes</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Premium Action Buttons */}
                      <div className="space-y-4">
                        {/* Clear All Button */}
                        <Button
                          variant="destructive"
                          onClick={clearAllPhotos}
                          disabled={capturedPhotos.length === 0}
                          className="w-full h-14 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white font-bold rounded-2xl shadow-2xl shadow-red-500/20 transition-all duration-300 disabled:opacity-50 disabled:shadow-none border-0 group"
                          size="default"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-white/20 rounded-xl group-hover:bg-white/30 transition-all duration-200">
                              <Trash2 className="h-5 w-5" />
                            </div>
                            <span className="text-base">Effacer Toutes les Photos</span>
                          </div>
                        </Button>
                          {/* Save Button */}
                        <Button
                          onClick={saveEnrollment}
                          disabled={!canSave || isSubmitting}
                          className="w-full h-16 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 text-white font-bold rounded-2xl shadow-2xl shadow-emerald-500/20 transition-all duration-300 disabled:opacity-50 disabled:from-slate-300 disabled:to-slate-400 disabled:shadow-none border-0 group relative overflow-hidden"
                          size="default"
                        >
                          {(canSave && !isSubmitting) && (
                            <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-green-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
                          )}
                          <div className="flex items-center space-x-4 relative z-10">
                            <div className={`p-3 rounded-xl transition-all duration-200 ${
                              canSave && !isSubmitting ? "bg-white/20 group-hover:bg-white/30" : "bg-slate-500/20"
                            }`}>
                              {isSubmitting ? (
                                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              ) : (
                                <Save className="h-6 w-6" />
                              )}
                            </div>
                            <div className="text-left">
                              <div className="text-lg font-bold">
                                {isSubmitting ? "🔄 Traitement en cours..." : canSave ? "✅ Valider l'Enrôlement" : "Enrôlement Incomplet"}
                              </div>
                              <div className="text-sm opacity-80">
                                {isSubmitting ? "Upload et traitement des photos..." : canSave ? "Sauvegarder les données biométriques" : `${6 - capturedPhotos.length} photos manquantes`}
                              </div>
                            </div>
                          </div>
                        </Button>
                      </div>
                      
                      {/* Premium Tips Panel
                      <div className="bg-gradient-to-br from-indigo-50/80 to-purple-50/80 backdrop-blur-sm border border-indigo-200/50 rounded-2xl p-4 shadow-lg">
                        <div className="flex items-center space-x-3 mb-3">
                          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                            <span className="text-white text-sm font-bold">💡</span>
                          </div>
                          <h6 className="font-bold text-indigo-800">Conseils de Capture Premium</h6>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-indigo-700">
                          <div className="flex items-center space-x-2">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></div>
                            <span>Éclairage optimal</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></div>
                            <span>Contact visuel direct</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></div>
                            <span>Angles variés</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></div>
                            <span>Ombres minimales</span>
                          </div>
                        </div>
                      </div> */}
                    </div>
                  </div>
                </div>
                </CardContent>
            </Card>
          </>
        )}    

        {/* Composant d'aide pour les raccourcis clavier */}
        <KeyboardShortcutsHelp 
          isOpen={showKeyboardHelp} 
          onClose={() => setShowKeyboardHelp(false)} 
        />
        
        {/* Guide de bienvenue au chargement */}
        <WelcomeGuide 
          isOpen={showWelcomeGuide} 
          onClose={() => setShowWelcomeGuide(false)} 
        />
      </div>
    </MainLayout>
  );
};

export default FaceEnrollment;
