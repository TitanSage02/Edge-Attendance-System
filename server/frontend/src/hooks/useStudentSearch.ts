import { useState, useMemo, useCallback } from 'react';
import { useDebounce } from './useDebounce';
import { StudentRead } from '@/types/studentTypes';

export interface UseStudentSearchParams {
  students: StudentRead[];
  isLoading: boolean;
}

export interface StudentSearchFilters {
  search: string;
  classFilter: string;
}

export interface UseStudentSearchResult {
  // État de recherche
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  debouncedSearchQuery: string;
  
  // Filtres
  filters: StudentSearchFilters;
  setFilters: (filters: Partial<StudentSearchFilters>) => void;
  
  // Résultats filtrés
  filteredStudents: StudentRead[];
  
  // Utilitaires
  clearSearch: () => void;
  clearFilters: () => void;
  isSearching: boolean;
  hasActiveFilters: boolean;
  
  // Nouvelles fonctionnalités
  searchStats: {
    total: number;
    filtered: number;
    hasFilter: boolean;
  };
  suggestions: string[];
  hasResults: boolean;
}

/**
 * Hook personnalisé pour la recherche et le filtrage fluides des apprenants
 * Combine debounce, filtrage multi-critères, recherche fuzzy et optimisations de performance
 */
export function useStudentSearch(params: UseStudentSearchParams): UseStudentSearchResult {
  const { students, isLoading } = params;
  
  // État de recherche principal
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
    // États des filtres
  const [filters, setFiltersState] = useState<StudentSearchFilters>({
    search: '',
    classFilter: 'all'
  });

  // Fonction pour mettre à jour les filtres
  const setFilters = useCallback((newFilters: Partial<StudentSearchFilters>) => {
    setFiltersState(prev => ({ ...prev, ...newFilters }));
  }, []);

  // Mise à jour du filtre de recherche quand la recherche débouncée change
  useMemo(() => {
    setFilters({ search: debouncedSearchQuery });
  }, [debouncedSearchQuery, setFilters]);

  // Fonction de recherche fuzzy améliorée
  const fuzzyMatch = useCallback((text: string, query: string): { matches: boolean; score: number } => {
    const textLower = text.toLowerCase();
    const queryLower = query.toLowerCase();
    
    // Recherche exacte (score le plus élevé)
    if (textLower.includes(queryLower)) {
      const exactIndex = textLower.indexOf(queryLower);
      // Score plus élevé si la correspondance est au début
      const score = exactIndex === 0 ? 100 : 80;
      return { matches: true, score };
    }

    // Recherche fuzzy : vérifie si tous les caractères de la requête 
    // apparaissent dans l'ordre dans le texte
    let queryIndex = 0;
    let lastMatchIndex = -1;
    let consecutiveMatches = 0;
    
    for (let i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
      if (textLower[i] === queryLower[queryIndex]) {
        if (i === lastMatchIndex + 1) {
          consecutiveMatches++;
        } else {
          consecutiveMatches = 1;
        }
        lastMatchIndex = i;
        queryIndex++;
      }
    }
    
    if (queryIndex === queryLower.length) {
      // Score basé sur le nombre de correspondances consécutives
      const score = Math.min(60, 20 + (consecutiveMatches * 10));
      return { matches: true, score };
    }
    
    return { matches: false, score: 0 };
  }, []);

  // Logique de filtrage optimisée avec scoring
  const filteredStudents = useMemo(() => {
    if (isLoading || !students) return [];

    let results = students;

    // Filtrage par recherche textuelle avec scoring
    if (filters.search.trim()) {
      const searchTerm = filters.search.trim();
      
      const scoredResults = students.map((student) => {
        const searchFields = [
          { value: student.id || '', weight: 10 },
          { value: student.firstName, weight: 8 },
          { value: student.lastName, weight: 8 },
          { value: `${student.firstName} ${student.lastName}`, weight: 9 },
          { value: `${student.lastName} ${student.firstName}`, weight: 7 },
          { value: student.classGroup, weight: 5 },
          { value: student.rfidUid || '', weight: 6 }
        ];

        let bestScore = 0;
        let hasMatch = false;

        searchFields.forEach(({ value, weight }) => {
          const { matches, score } = fuzzyMatch(value, searchTerm);
          if (matches) {
            hasMatch = true;
            bestScore = Math.max(bestScore, score * (weight / 10));
          }
        });

        return { student, score: bestScore, matches: hasMatch };
      })
      .filter(result => result.matches)
      .sort((a, b) => b.score - a.score)
      .map(result => result.student);

      results = scoredResults;
    }    // Filtrage par classe
    if (filters.classFilter !== 'all') {
      results = results.filter(student => student.classGroup === filters.classFilter);
    }

    return results;
  }, [students, filters, isLoading, fuzzyMatch]);
  // Statistiques de recherche
  const searchStats = useMemo(() => {
    const hasFilter = filters.search.trim() !== '' || filters.classFilter !== 'all';
    
    return {
      total: students?.length || 0,
      filtered: filteredStudents?.length || 0,
      hasFilter
    };
  }, [students, filteredStudents, filters]);

  // Suggestions de recherche intelligentes
  const suggestions = useMemo(() => {
    if (!students || searchQuery.length < 2) {
      return [];
    }

    const uniqueValues = new Set<string>();
    
    students.forEach(student => {
      // Ajouter les classes
      if (student.classGroup && student.classGroup.toLowerCase().includes(searchQuery.toLowerCase())) {
        uniqueValues.add(student.classGroup);
      }
      
      // Ajouter les noms et prénoms
      if (student.firstName && student.firstName.toLowerCase().includes(searchQuery.toLowerCase())) {
        uniqueValues.add(student.firstName);
      }
      if (student.lastName && student.lastName.toLowerCase().includes(searchQuery.toLowerCase())) {
        uniqueValues.add(student.lastName);
      }
      
      // Ajouter les noms complets
      const fullName = `${student.firstName} ${student.lastName}`;
      if (fullName.toLowerCase().includes(searchQuery.toLowerCase())) {
        uniqueValues.add(fullName);
      }
    });

    return Array.from(uniqueValues)
      .filter(value => value.toLowerCase() !== searchQuery.toLowerCase())
      .slice(0, 5); // Limiter à 5 suggestions
  }, [students, searchQuery]);

  // Fonctions utilitaires
  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);
  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFiltersState({
      search: '',
      classFilter: 'all'
    });
  }, []);
  // États dérivés
  const isSearching = debouncedSearchQuery.trim().length > 0;
  const hasActiveFilters = filters.classFilter !== 'all' || isSearching;
  const hasResults = (filteredStudents?.length || 0) > 0;

  return {
    searchQuery,
    setSearchQuery,
    debouncedSearchQuery,
    filters,
    setFilters,
    filteredStudents,
    clearSearch,
    clearFilters,
    isSearching,
    hasActiveFilters,
    searchStats,
    suggestions,
    hasResults
  };
}
