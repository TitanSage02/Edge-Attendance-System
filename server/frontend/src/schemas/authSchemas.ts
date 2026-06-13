import { z } from "zod";
import { PASSWORD_CRITERIA, validatePassword } from "@/utils/passwordValidation";

/**
 * Schéma de validation pour le formulaire de connexion
 */
export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "L'email est requis")
    .email("Format d'email invalide")
    .max(255, "L'email ne peut pas dépasser 255 caractères"),
  
  password: z
    .string()
    .min(1, "Le mot de passe est requis")
    .min(6, "Le mot de passe doit contenir au moins 6 caractères")
    .max(128, "Le mot de passe ne peut pas dépasser 128 caractères"),
    
  rememberMe: z.boolean().optional()
});

/**
 * Schéma de validation pour le formulaire de réinitialisation de mot de passe
 */
export const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, "L'email est requis")
    .email("Format d'email invalide")
    .max(255, "L'email ne peut pas dépasser 255 caractères")
});

/**
 * Schéma de validation pour le changement de mot de passe
 */
export const changePasswordSchema = z.object({
  currentPassword: z
    .string()
    .min(1, "Le mot de passe actuel est requis"),
  newPassword: z
    .string()
    .min(1, "Le nouveau mot de passe est requis")
    .max(128, "Le mot de passe ne peut pas dépasser 128 caractères")
    .superRefine((password, ctx) => {
      // Validation directe avec les mêmes critères que l'affichage
      const failedCriteria = PASSWORD_CRITERIA.filter(criterion => !criterion.test(password));
      
      if (failedCriteria.length > 0) {
        // Ajouter une seule erreur globale au lieu d'une erreur par critère
        const failedLabels = failedCriteria.map(c => c.label).join(", ");
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Critères manquants: ${failedLabels}`,
        });
      }
    }),
    
  confirmPassword: z
    .string()
    .min(1, "La confirmation du mot de passe est requise")
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Les mots de passe ne correspondent pas",
  path: ["confirmPassword"]
});

// Types TypeScript générés à partir des schémas
export type LoginFormData = z.infer<typeof loginSchema>;
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

// Fonction utilitaire pour valider un champ spécifique
export const validateField = <T extends z.ZodRawShape>(
  schema: z.ZodObject<T>,
  fieldName: keyof z.infer<z.ZodObject<T>>,
  value: any
): string | null => {
  try {
    const fieldSchema = schema.shape[fieldName];
    fieldSchema.parse(value);
    return null;
  } catch (error) {
    if (error instanceof z.ZodError) {
      return error.errors[0]?.message || "Erreur de validation";
    }
    return "Erreur de validation";
  }
};
