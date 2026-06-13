import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { PASSWORD_CRITERIA, getPasswordStrength } from "@/utils/passwordValidation";

interface PasswordStrengthIndicatorProps {
  password: string;
  className?: string;
}

export const PasswordStrengthIndicator = ({ password, className }: PasswordStrengthIndicatorProps) => {
  // Calcul unique des critères respectés
  const evaluatedCriteria = PASSWORD_CRITERIA.map(criterion => ({
    ...criterion,
    met: criterion.test(password)
  }));
  
  const metRequirements = evaluatedCriteria.filter(c => c.met).length;
  const progressPercentage = getPasswordStrength(password);

  const getStrengthText = () => {
    if (metRequirements === 0) return "Aucune exigence";
    if (metRequirements <= 2) return "Faible";
    if (metRequirements <= 3) return "Moyen";
    if (metRequirements <= 4) return "Fort";
    return "Très fort";
  };
  const getStrengthColor = () => {
    if (metRequirements <= 2) return "text-red-500";
    if (metRequirements <= 3) return "text-orange-500";
    if (metRequirements <= 4) return "text-yellow-500";
    return "text-green-500";
  };

  if (!password) return null;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-600">Force du mot de passe</span>
        <span className={cn("text-sm font-medium", getStrengthColor())}>
          {getStrengthText()}
        </span>
      </div>
      <Progress 
        value={progressPercentage} 
        className="h-2"
      />      
      <p className="text-xs text-gray-500">
        {metRequirements} sur {PASSWORD_CRITERIA.length} exigences respectées
      </p>
    </div>
  );
};
