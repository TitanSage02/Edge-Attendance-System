import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SearchInputProps {
  /** Valeur actuelle de la recherche */
  value: string;
  /** Fonction appelée lors du changement de valeur */
  onChange: (value: string) => void;
  /** Fonction appelée pour effacer la recherche */
  onClear?: () => void;
  /** Placeholder du champ de recherche */
  placeholder?: string;
  /** Indique si une recherche est en cours */
  isLoading?: boolean;
  /** Indique si le debouncing est en cours */
  isDebouncing?: boolean;
  /** Classes CSS additionnelles */
  className?: string;
  /** Taille du composant */
  size?: "sm" | "md" | "lg";
  /** Désactive le champ de recherche */
  disabled?: boolean;
  /** Affiche le nombre de résultats */
  resultCount?: number;
  /** Texte personnalisé pour les résultats */
  resultText?: string;
}

/**
 * Composant de recherche avancé avec indicateurs visuels
 */
export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  onClear,
  placeholder = "Rechercher...",
  isLoading = false,
  isDebouncing = false,
  className,
  size = "md",
  disabled = false,
  resultCount,
  resultText
}) => {
  const sizeClasses = {
    sm: "h-8 text-xs",
    md: "h-10 text-sm", 
    lg: "h-12 text-base"
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5"
  };

  const showClearButton = value.length > 0 && !disabled;
  const showLoadingIndicator = isLoading || isDebouncing;

  return (
    <div className={cn("relative flex flex-col gap-1", className)}>
      <div className="relative">
        {/* Icône de recherche */}
        <Search className={cn(
          "absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-500",
          iconSizes[size]
        )} />

        {/* Champ de saisie */}
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "pl-8",
            showClearButton ? "pr-16" : "pr-3",
            sizeClasses[size]
          )}
        />

        {/* Boutons et indicateurs à droite */}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
          {/* Indicateur de chargement */}
          {showLoadingIndicator && (
            <Loader2 className={cn(
              "animate-spin text-gray-500",
              iconSizes[size]
            )} />
          )}

          {/* Bouton d'effacement */}
          {showClearButton && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={cn(
                "text-gray-500 hover:text-gray-700",
                size === "sm" ? "h-6 w-6" : size === "lg" ? "h-8 w-8" : "h-7 w-7"
              )}
              onClick={onClear}
              title="Effacer la recherche"
            >
              <X className={iconSizes[size]} />
            </Button>
          )}
        </div>
      </div>

      {/* Compteur de résultats */}
      {resultCount !== undefined && value.length > 0 && !isDebouncing && (
        <div className="text-xs text-gray-500 px-1">
          {resultCount > 0 ? (
            <>
              {resultCount} {resultText || "résultat(s)"} trouvé(s)
              {value && (
                <span className="ml-1">
                  pour "<span className="font-medium">{value}</span>"
                </span>
              )}
            </>
          ) : (
            <>
              Aucun résultat trouvé
              {value && (
                <span className="ml-1">
                  pour "<span className="font-medium">{value}</span>"
                </span>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchInput;
