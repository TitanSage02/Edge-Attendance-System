import { useState, useEffect, useCallback, useMemo } from "react";

export interface UseSearchOptions {
  /** Délai de debounce en millisecondes (par défaut: 300ms) */
  debounceMs?: number;
  /** Longueur minimale avant de déclencher la recherche (par défaut: 0) */
  minLength?: number;
  /** Fonction de transformation de la requête de recherche */
  transform?: (query: string) => string;
}

export interface UseSearchResult {
  /** Valeur actuelle du champ de recherche */
  query: string;
  /** Valeur debouncée utilisée pour les requêtes */
  debouncedQuery: string;
  /** Fonction pour mettre à jour la requête */
  setQuery: (query: string) => void;
  /** Fonction pour effacer la recherche */
  clearQuery: () => void;
  /** Indique si la recherche est en cours de debounce */
  isDebouncing: boolean;
  /** Indique si la recherche est active (longueur minimale atteinte) */
  isSearchActive: boolean;
}

/**
 * Hook personnalisé pour gérer la recherche avec debouncing
 * et des fonctionnalités avancées
 */
export function useSearch(options: UseSearchOptions = {}): UseSearchResult {
  const {
    debounceMs = 300,
    minLength = 0,
    transform = (query: string) => query.trim().toLowerCase()
  } = options;

  const [query, setQueryState] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [isDebouncing, setIsDebouncing] = useState(false);

  // Gestion du debouncing
  useEffect(() => {
    const transformedQuery = transform(query);
    
    if (transformedQuery.length >= minLength) {
      setIsDebouncing(true);
      
      const timer = setTimeout(() => {
        setDebouncedQuery(transformedQuery);
        setIsDebouncing(false);
      }, debounceMs);

      return () => {
        clearTimeout(timer);
        setIsDebouncing(false);
      };
    } else {
      // Si la longueur minimale n'est pas atteinte, on efface immédiatement
      setDebouncedQuery("");
      setIsDebouncing(false);
    }
  }, [query, debounceMs, minLength, transform]);

  // Fonctions d'utilitaire
  const setQuery = useCallback((newQuery: string) => {
    setQueryState(newQuery);
  }, []);

  const clearQuery = useCallback(() => {
    setQueryState("");
    setDebouncedQuery("");
    setIsDebouncing(false);
  }, []);

  // État calculé
  const isSearchActive = useMemo(() => {
    return debouncedQuery.length >= minLength;
  }, [debouncedQuery, minLength]);

  return {
    query,
    debouncedQuery,
    setQuery,
    clearQuery,
    isDebouncing,
    isSearchActive
  };
}

/**
 * Hook pour filtrer des données localement avec recherche
 */
export function useLocalSearch<T>(
  data: T[],
  searchFields: (keyof T | ((item: T) => string))[],
  searchOptions?: UseSearchOptions
) {
  const search = useSearch(searchOptions);
  
  const filteredData = useMemo(() => {
    if (!search.isSearchActive || !data) {
      return data;
    }

    const searchTerm = search.debouncedQuery.toLowerCase();
    
    return data.filter((item) => {
      return searchFields.some((field) => {
        let value: string;
        
        if (typeof field === 'function') {
          value = field(item);
        } else {
          value = String(item[field] || '');
        }
        
        return value.toLowerCase().includes(searchTerm);
      });
    });
  }, [data, search.debouncedQuery, search.isSearchActive, searchFields]);

  return {
    ...search,
    filteredData,
    resultCount: filteredData?.length || 0,
    hasResults: (filteredData?.length || 0) > 0
  };
}
