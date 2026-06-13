import { Module } from '@/types/moduleTypes';

/**
 * Service pour gérer les modules auto-enregistrés
 */
export class ModuleAutoRegistrationService {
  /**
   * Vérifie si un module est auto-enregistré (sans configuration complète)
   */
  static isAutoRegistered(module: Module): boolean {
    return (
      module.name?.startsWith('Module ') ||
      module.description === 'Module auto-enregistré' ||
      module.emplacement === 'Non spécifié'
    );
  }

  /**
   * Identifie les modules nécessitant une configuration
   */
  static needsConfiguration(modules: Module[]): Module[] {
    return modules.filter(this.isAutoRegistered);
  }

  /**
   * Formate les informations d'un module auto-enregistré pour l'affichage
   */
  static formatAutoRegisteredModule(module: Module): Module & { needsConfig: boolean } {
    return {
      ...module,
      needsConfig: this.isAutoRegistered(module),
    };
  }

  /**
   * Génère un nom suggéré pour un module auto-enregistré
   */
  static suggestModuleName(module: Module): string {
    if (module.emplacement && module.emplacement !== 'Non spécifié') {
      return `Module ${module.emplacement}`;
    }
    return `Module ${module.uid}`;
  }

  /**
   * Valide si les données de configuration d'un module sont complètes
   */
  static validateModuleConfiguration(module: Partial<Module>): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (!module.name || module.name.trim() === '' || module.name.startsWith('Module ')) {
      errors.push('Le nom du module doit être personnalisé');
    }

    if (!module.emplacement || module.emplacement === 'Non spécifié') {
      errors.push('L\'emplacement du module doit être spécifié');
    }

    if (!module.description || module.description === 'Module auto-enregistré') {
      errors.push('La description du module doit être personnalisée');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}
