import React, { useState, useMemo, useEffect } from "react";
import MainLayout from "../components/layout/MainLayout";

import { useStudents } from "@/hooks/useStudents";
import { useSettings } from "@/hooks/useSettings";
import { useStudentSearch } from "@/hooks/useStudentSearch";
import { StudentRead, StudentUpdate, StudentBase } from "@/types/studentTypes";
import { SearchInput } from "@/components/ui/search-input";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Trash2, UserPlus, Edit, RefreshCw, Filter, Camera, Plus } from "lucide-react";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { AddStudentForm } from "@/components/students/AddStudentForm";
import { EditStudentForm } from "@/components/students/EditStudentForm";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";

// Interface for the data coming from AddStudentForm
interface StudentFormDataFromForm {
  student_id: string;
  first_name: string;
  last_name: string;
  class_name: string;
  rfid_card?: string;
}

const Apprenants = () => {
  const { success, error: showError } = useUnifiedToast();
  const navigate = useNavigate();

  // États pour la pagination et la gestion des dialogues
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<StudentRead | null>(null);
  
  const studentsPerPage = 15;

  // Récupération des données des apprenants sans filtrage côté serveur pour la recherche fluide
  const {
    studentsPage,
    isLoading,
    create,
    update,
    remove,
  } = useStudents({
    page: currentPage,
    limit: studentsPerPage,
  });  
  // Hook de recherche avancée avec tous les apprenants
  const {
    searchQuery,
    setSearchQuery,
    filteredStudents,
    isSearching,
    clearSearch,
    suggestions,
    searchStats
  } = useStudentSearch({
    students: studentsPage?.items || [],
    isLoading
  });  
  // États pour les filtres additionnels
  const [classFilter, setClassFilter] = useState<string>("all");

  // Application des filtres additionnels sur les résultats de recherche
  const finalFilteredStudents = useMemo(() => {
    let results = filteredStudents;

    // Filtre par classe
    if (classFilter !== "all") {
      results = results.filter(student => student.classGroup === classFilter);
    }

    return results;
  }, [filteredStudents, classFilter]);

  // Vérifier s'il y a des filtres actifs
  const hasActiveFilters = classFilter !== "all";

  // Fonction pour effacer tous les filtres
  const clearAllFilters = () => {
    setClassFilter("all");
    clearSearch();
  };
  // Gestion de la pagination des résultats finaux
  const paginatedStudents = useMemo(() => {
    const startIndex = (currentPage - 1) * studentsPerPage;
    const endIndex = startIndex + studentsPerPage;
    return finalFilteredStudents.slice(startIndex, endIndex);
  }, [finalFilteredStudents, currentPage, studentsPerPage]);

  const totalFilteredItems = finalFilteredStudents.length;
  const totalFilteredPages = Math.ceil(totalFilteredItems / studentsPerPage);
  // Reset de la page quand les filtres changent
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, classFilter]);

  // Récupération des classes uniques pour les filtres
  const allClassGroups = useMemo(() => {
    if (!studentsPage?.items) return [];
    return Array.from(
      new Set(
        studentsPage.items
          .map(s => s.classGroup)
          .filter(Boolean)
          .sort()
      )
    );
  }, [studentsPage?.items]); 
  
  // Récupérer la promotion depuis les paramètres système
  const { settings, refreshSettings } = useSettings();
  const promotion = useMemo(() => {
    return settings?.system?.current_promotion || "";
  }, [settings?.system?.current_promotion]);

  // Écouter les changements de promotion
  useEffect(() => {
    const handlePromotionUpdated = () => {
      // Rafraîchir les paramètres pour obtenir la nouvelle promotion
      refreshSettings();
    };

    // Ajouter l'écouteur d'événement
    window.addEventListener('settings:promotion_updated', handlePromotionUpdated);
    
    // Nettoyer l'écouteur d'événement
    return () => {
      window.removeEventListener('settings:promotion_updated', handlePromotionUpdated);
    };
  }, [refreshSettings]);
  const handleDeleteStudent = async (id: string) => {
    try {
      await remove.mutateAsync(id);
      success(`L'apprenant avec l'ID ${id} a été supprimé.`, { title: "Apprenant supprimé" });
    } catch (error) {
      showError("Impossible de supprimer l'apprenant.", { title: "Erreur de suppression" });
    }
  };

  const handleUpdateEmbeddings = async (student: StudentRead) => {    try {
      await update.mutateAsync({ id: student.id!, data: { faceEnrolled: false } });
      success(`Reprise des embeddings pour ${student.firstName} ${student.lastName} demandée.`, { title: "Mise à jour demandée" });
      
      // TODO : Redirection vers la page d'enrôlement 
      // Il sera question d'une page où on va pouvoir sélectionner une caméra branchée au PC, 
      // tenir compte des infos d'apprennants affichés à droite de l'interface pour faire la photo et saisir l'ID RFID si c'était pas mis auparavant.. 

    } catch (error) {
      showError("Impossible de demander la mise à jour.", { title: "Erreur" });
    }
  };
  const handleAddStudent = async (dataFromForm: StudentFormDataFromForm) => {
    try {
      // Utilisez la promotion des paramètres système
      const newStudentData: StudentBase = {
        id: dataFromForm.student_id,
        firstName: dataFromForm.first_name,
        lastName: dataFromForm.last_name,
        classGroup: dataFromForm.class_name,
        promotion: promotion, // Promotion des paramètres système
        rfidUid: dataFromForm.rfid_card || null,
        faceEnrolled: false, // Par défaut pour les nouveaux apprenants 
      };if (!newStudentData.id ||!newStudentData.firstName || !newStudentData.lastName || !newStudentData.classGroup) {
        showError("ID, Nom, prénom et classe sont requis.", { title: "Erreur de validation" });
        return;
      }
      
      await create.mutateAsync(newStudentData); // Ajout de l'apprenant
      
      success(`${newStudentData.firstName} ${newStudentData.lastName} a été ajouté.`, { title: "Apprenant ajouté" });
    } catch (error) {
      showError("Impossible d'ajouter l'apprenant.", { title: "Erreur d'ajout" });
    }
  };
  const handleEditStudent = async (id: string, dataFromForm: Partial<StudentUpdate>) => {
    try {
      await update.mutateAsync({ id, data: dataFromForm });
      success("Les informations ont été mises à jour.", { title: "Apprenant modifié" });
      setIsEditDialogOpen(false);
    } catch (error) {
      showError("Impossible de modifier l'apprenant.", { title: "Erreur de modification" });
    }
  };

  if (isLoading && !studentsPage) {
    return <MainLayout>
            <div className="p-4 text-center">
              Chargement des apprenants en cours...
              </div>
           </MainLayout>;
  }

  return (
    <MainLayout requiredRoles={["admin", "pedagogical"]}>
    <div className="space-y-6">        
      <div className="flex flex-col sm:flex-row justify-between gap-3 sm:items-center">
          <h1 className="text-2xl font-bold tracking-tight">Gestion des Apprenants</h1>
          <div className="flex flex-wrap gap-2">
            <Button 
              onClick={() => navigate('/enrollment')}
              className="bg-orange-500 hover:bg-orange-600 text-white"
              size="sm"
            >
              <Camera className="h-4 w-4 mr-1.5" />
              <span className="whitespace-nowrap">Enrôlement des visages</span>
            </Button>
            <AddStudentForm 
              onAddStudent={handleAddStudent} 
              classGroups={allClassGroups}
            >
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1.5" />
                <span className="whitespace-nowrap">Ajouter un apprenant</span>
              </Button>
            </AddStudentForm>
          </div>
        </div>

        <div className="bg-blue-50 p-4 rounded-md">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Promotion en cours</h3>
              <p className="text-blue-700 font-semibold">{promotion}</p>
            </div>
          </div>
        </div>        
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          {/* Barre de recherche avancée */}
          <div className="flex-1 max-w-md">            
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              onClear={clearSearch}
              placeholder="Rechercher par nom, prénom, ID ou RFID..."
              isLoading={isSearching}
              resultCount={finalFilteredStudents.length}
              size="md"
            />
          </div>          
          {/* Filtres et actions */}
          <div className="flex flex-wrap gap-2 items-center">
            <Select
              value={classFilter}
              onValueChange={setClassFilter}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Classe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Toutes les classes</SelectItem>
                {allClassGroups.map((group) => (
                  <SelectItem key={group} value={group}>
                    {group}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {(hasActiveFilters || searchQuery) && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFilters}
                className="text-gray-600"
              >
                <Filter className="h-4 w-4 mr-1" />
                Effacer filtres
              </Button>
            )}
          </div>
        </div>        
        {/* Indicateurs de recherche et résultats avec statistiques avancées */}
        {(isSearching || hasActiveFilters || searchQuery) && (
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <div className="text-blue-700">
                {searchQuery && (
                  <span>Recherche: "<strong>{searchQuery}</strong>" • </span>
                )}
                <strong>{totalFilteredItems}</strong> apprenant(s) trouvé(s)
                {totalFilteredItems !== (studentsPage?.total_items || 0) && (
                  <span className="text-blue-600"> sur {studentsPage?.total_items || 0} au total</span>
                )}
              </div>
              {(hasActiveFilters || searchQuery) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllFilters}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Afficher tous
                </Button>
              )}
            </div>
            {/* Affichage des suggestions si disponibles */}
            {suggestions && suggestions.length > 0 && !searchQuery && (
              <div className="mt-2 pt-2 border-t border-blue-200">
                <div className="text-xs text-blue-600 mb-1">Suggestions de recherche :</div>
                <div className="flex flex-wrap gap-1">
                  {suggestions.slice(0, 5).map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => setSearchQuery(suggestion)}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}<div className="rounded-lg border shadow">
          {isLoading && <div className="p-4 text-center">Chargement...</div>}
          {!isLoading && paginatedStudents.length === 0 && (
            <div className="p-4 text-center text-gray-500">Aucun apprenant trouvé pour les critères sélectionnés.</div>
          )}
          {!isLoading && paginatedStudents.length > 0 && (
            <Table>
              <TableHeader className="bg-white rounded-lg">
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Nom</TableHead>
                  <TableHead>Prénom</TableHead>
                  <TableHead>UID RFID</TableHead>
                  <TableHead>Classe</TableHead>
                  <TableHead>Visage Enrôlé</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedStudents.map((student) => (
                  <TableRow key={student.id!}>
                    <TableCell className="font-medium">{student.id}</TableCell>
                    <TableCell>{student.lastName}</TableCell>
                    <TableCell>{student.firstName}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 text-xs rounded-full ${student.rfidUid ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"}`}>
                        {student.rfidUid || "Non défini"}
                      </span>
                    </TableCell>
                    <TableCell>{student.classGroup}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 text-xs rounded-full ${student.faceEnrolled ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                        {student.faceEnrolled ? "Oui" : "Non"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-1">
                        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                          <DialogTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              title="Modifier"
                              onClick={() => {
                                setSelectedStudent(student);
                                setIsEditDialogOpen(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Modifier l'apprenant</DialogTitle>
                              <DialogDescription>
                                Modifiez les informations de {student.firstName} {student.lastName}.
                              </DialogDescription>
                            </DialogHeader>
                            {selectedStudent && (
                              <EditStudentForm 
                                student={selectedStudent} 
                                onSubmit={(data) => handleEditStudent(selectedStudent.id!, data)} 
                                classGroups={allClassGroups}
                              />
                            )}
                          </DialogContent>
                        </Dialog>

                        <Button variant="ghost" size="icon" title="Ré-enrôler le visage" onClick={() => handleUpdateEmbeddings(student)}>
                          <RefreshCw className="h-4 w-4" />
                        </Button>

                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="icon" title="Supprimer">
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Êtes-vous sûr ?</AlertDialogTitle>
                              <AlertDialogDescription>
                                Cette action ne peut pas être annulée. Cela supprimera définitivement l'apprenant {student.firstName} {student.lastName}.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Annuler</AlertDialogCancel>
                              <AlertDialogAction onClick={() => handleDeleteStudent(student.id!)} className="bg-red-500 hover:bg-red-600">
                                Supprimer
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>        
        {totalFilteredPages > 1 && (
          <div className="flex justify-between items-center pt-4">
            <div className="text-sm text-gray-500">
              Page {currentPage} sur {totalFilteredPages}.
              {(hasActiveFilters || searchQuery) ? (
                <span> {totalFilteredItems} apprenant(s) trouvé(s) sur {studentsPage?.total_items || 0} au total.</span>
              ) : (
                <span> Total: {totalFilteredItems} apprenant(s).</span>
              )}
            </div>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(c => Math.max(1, c - 1))} 
                disabled={currentPage === 1}
              >
                Précédent
              </Button>
              {[...Array(Math.min(5, totalFilteredPages)).keys()].map((_, index) => {
                // Logique pour afficher les pages pertinentes autour de la page actuelle
                let pageNumber;
                if (totalFilteredPages <= 5) {
                  pageNumber = index + 1;
                } else if (currentPage <= 3) {
                  pageNumber = index + 1;
                } else if (currentPage >= totalFilteredPages - 2) {
                  pageNumber = totalFilteredPages - 4 + index;
                } else {
                  pageNumber = currentPage - 2 + index;
                }

                return (
                  <Button
                    key={pageNumber}
                    variant={pageNumber === currentPage ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(pageNumber)}
                  >
                    {pageNumber}
                  </Button>
                );
              })}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setCurrentPage(c => Math.min(totalFilteredPages, c + 1))} 
                disabled={currentPage === totalFilteredPages}
              >
                Suivant
              </Button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default Apprenants;