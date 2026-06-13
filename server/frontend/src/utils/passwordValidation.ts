/**
 * Configuration centralisée des critères de validation des mots de passe
 * Source unique de vérité utilisée par Zod et les composants UI
 */

export interface PasswordCriterion {
  label: string;
  test: (password: string) => boolean;
  errorMessage: string;
}

export const PASSWORD_CRITERIA: PasswordCriterion[] = [
  {
    label: "Au moins 8 caractères",
    test: (pwd) => pwd.length >= 8,
    errorMessage: "Le mot de passe doit contenir au moins 8 caractères"
  },
  {
    label: "Au moins une lettre majuscule",
    test: (pwd) => /[A-Z]/.test(pwd),
    errorMessage: "Le mot de passe doit contenir au moins une lettre majuscule"
  },
  {
    label: "Au moins une lettre minuscule",
    test: (pwd) => /[a-z]/.test(pwd),
    errorMessage: "Le mot de passe doit contenir au moins une lettre minuscule"
  },
  {
    label: "Au moins un chiffre",
    test: (pwd) => /[0-9]/.test(pwd),
    errorMessage: "Le mot de passe doit contenir au moins un chiffre"
  },
  {
    label: "Au moins un caractère spécial",
    test: (pwd) => /[!@#$%^&*(),.?":{}|<>]/.test(pwd),
    errorMessage: "Le mot de passe doit contenir au moins un caractère spécial"
  }
];

/**
 * Valide un mot de passe contre tous les critères
 */
export const validatePassword = (password: string): { isValid: boolean; failedCriteria: PasswordCriterion[] } => {
  const failedCriteria = PASSWORD_CRITERIA.filter(criterion => !criterion.test(password));
  
  return {
    isValid: failedCriteria.length === 0,
    failedCriteria
  };
};

/**
 * Retourne le pourcentage de critères respectés
 */
export const getPasswordStrength = (password: string): number => {
  const metCriteria = PASSWORD_CRITERIA.filter(criterion => criterion.test(password)).length;
  return (metCriteria / PASSWORD_CRITERIA.length) * 100;
};
