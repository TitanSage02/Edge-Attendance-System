import { useState, useEffect } from 'react';

/**
 * Hook personnalisé pour débouncer une valeur
 * Retarde la mise à jour de la valeur jusqu'à ce qu'elle reste stable pendant le délai spécifié
 * 
 * @param value - La valeur à débouncer
 * @param delay - Le délai en millisecondes (par défaut 300ms)
 * @returns La valeur débouncée
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Créer un timer qui met à jour la valeur débouncée après le délai
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Nettoyer le timer si la valeur change avant la fin du délai
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
