import React, { forwardRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface RfidUidInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value'> {
  value?: string;
  onChange?: (value: string) => void;
}

/**
 * Composant Input avec formatage automatique d'UID RFID
 * Format: XX:XX:XX:XX (8 caractères hexadécimaux avec deux-points automatiques)
 */
export const RfidUidInput = forwardRef<HTMLInputElement, RfidUidInputProps>(
  ({ className, value = "", onChange, ...props }, ref) => {
    const [displayValue, setDisplayValue] = useState(() => formatRfidUid(value));

    // Fonction pour formater l'UID RFID avec des deux-points
    function formatRfidUid(input: string): string {
      // Supprimer tous les caractères non hexadécimaux
      const cleanInput = input.replace(/[^A-Fa-f0-9]/g, '').toUpperCase();
      
      // Limiter à 8 caractères
      const limited = cleanInput.slice(0, 8);
      
      // Ajouter les deux-points tous les 2 caractères
      if (limited.length <= 2) {
        return limited;
      } else if (limited.length <= 4) {
        return `${limited.slice(0, 2)}:${limited.slice(2)}`;
      } else if (limited.length <= 6) {
        return `${limited.slice(0, 2)}:${limited.slice(2, 4)}:${limited.slice(4)}`;
      } else {
        return `${limited.slice(0, 2)}:${limited.slice(2, 4)}:${limited.slice(4, 6)}:${limited.slice(6)}`;
      }
    }

    // Fonction pour nettoyer l'UID RFID (supprimer les deux-points pour la valeur brute)
    function cleanRfidUid(formatted: string): string {
      return formatted.replace(/[^A-Fa-f0-9]/g, '').toUpperCase();
    }

    // Gérer les changements de saisie
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value;
      const formatted = formatRfidUid(inputValue);
      const cleaned = cleanRfidUid(formatted);
      
      setDisplayValue(formatted);
      
      // Appeler onChange avec la valeur nettoyée (sans deux-points)
      if (onChange) {
        onChange(cleaned);
      }
    };

    // Gérer les changements de valeur externe
    React.useEffect(() => {
      const formatted = formatRfidUid(value || "");
      setDisplayValue(formatted);
    }, [value]);

    // Gérer la validation visuelle
    const cleanLength = cleanRfidUid(displayValue).length;
    const isComplete = cleanLength === 8;
    const isEmpty = displayValue.length === 0;
    const isValid = isEmpty || (cleanLength >= 4 && cleanLength <= 8); // Au minimum 4 caractères, au maximum 8

    return (
      <div className="relative">
        <Input
          ref={ref}
          className={cn(
            "font-mono tracking-wider",
            isComplete && "ring-2 ring-green-500 border-green-500",
            !isEmpty && !isComplete && isValid && "ring-2 ring-yellow-500 border-yellow-500",
            !isEmpty && !isValid && "ring-2 ring-red-500 border-red-500",
            className
          )}
          value={displayValue}
          onChange={handleInputChange}
          placeholder="XX:XX:XX:XX"
          maxLength={11} // 8 caractères + 3 deux-points
          {...props}
        />
        
        {/* Indicateur de progression */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
          <div className="text-xs text-muted-foreground">
            {cleanLength}/8
          </div>
          {isComplete && (
            <div className="w-2 h-2 rounded-full bg-green-500" title="UID RFID complet" />
          )}
          {!isEmpty && !isComplete && isValid && (
            <div className="w-2 h-2 rounded-full bg-yellow-500" title="UID RFID valide mais incomplet" />
          )}
          {!isEmpty && !isValid && (
            <div className="w-2 h-2 rounded-full bg-red-500" title="UID RFID invalide" />
          )}
        </div>
        
        {/* Aide contextuelle */}
        {!isEmpty && (
          <div className="absolute -bottom-5 left-0 text-xs text-muted-foreground">
            {isComplete ? "UID RFID complet" : 
             isValid ? "Saisissez les caractères restants" : 
             "Uniquement des caractères hexadécimaux (0-9, A-F)"}
          </div>
        )}
      </div>
    );
  }
);

RfidUidInput.displayName = "RfidUidInput";
