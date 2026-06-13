import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  isLoading?: boolean;
}

/**
 * Composant de barre de recherche réutilisable avec fonctionnalités avancées
 * - Icône de recherche intégrée
 * - Bouton de suppression conditionnel
 * - Support des états de chargement et désactivé
 * - Styles personnalisables
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onClear,
  placeholder = "Rechercher...",
  className,
  disabled = false,
  isLoading = false,
}) => {
  const handleClear = () => {
    onChange('');
    onClear?.();
  };

  return (
    <div className={cn("relative flex-1", className)}>
      <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || isLoading}
        className={cn(
          "pl-8",
          value && "pr-8",
          isLoading && "opacity-50 cursor-not-allowed"
        )}
      />
      {value && !disabled && !isLoading && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1 h-6 w-6 text-gray-500 hover:text-gray-700"
          onClick={handleClear}
          title="Effacer la recherche"
          aria-label="Effacer la recherche"
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
};
