import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { PASSWORD_CRITERIA } from "@/utils/passwordValidation";

interface PasswordRequirementsProps {
  password: string;
  className?: string;
}

export const PasswordRequirements = ({ password, className }: PasswordRequirementsProps) => {
  // Calcul unique des critères pour éviter la duplication de logique
  const evaluatedCriteria = PASSWORD_CRITERIA.map(criterion => ({
    ...criterion,
    met: criterion.test(password)
  }));

  return (
    <div className={cn("space-y-2", className)}>
      <p className="text-sm font-medium text-gray-700">
        Exigences du mot de passe :
      </p>      
      <ul className="space-y-1">
        {evaluatedCriteria.map((criterion, index) => (
          <li
            key={index}
            className={cn(
              "flex items-center gap-2 text-sm transition-colors duration-200",
              criterion.met ? "text-green-600" : "text-gray-500"
            )}
          >
            <div
              className={cn(
                "flex items-center justify-center w-4 h-4 rounded-full transition-colors duration-200",
                criterion.met
                  ? "bg-green-100 text-green-600"
                  : "bg-gray-100 text-gray-400"
              )}
            >
              {criterion.met ? (
                <Check className="w-3 h-3" />
              ) : (
                <X className="w-3 h-3" />
              )}
            </div>
            <span className={criterion.met ? "font-medium" : ""}>{criterion.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
