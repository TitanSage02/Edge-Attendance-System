import { Permission } from "@/types/userTypes";

export const rolePermissions: Record<string, Permission[]> = {
  admin: [
    { name: "Gestion des utilisateurs", description: "Créer, modifier et supprimer des utilisateurs" },
    { name: "Gestion des modules", description: "Gérer tous les modules de présence" },
    { name: "Accès aux logs", description: "Voir toutes les activités du système" },
    { name: "Paramètres système", description: "Modifier les paramètres système" },
  ],
  pedagogical: [
    { name: "Gestion des apprenants", description: "Gérer les fiches des apprenants" },
    { name: "Suivi des présences", description: "Consulter et modifier les présences" },
    { name: "Rapports", description: "Générer des rapports de présence" },
  ],
  technician: [
    { name: "Maintenance des modules", description: "Surveiller et entretenir les modules" },
    { name: "Alertes techniques", description: "Recevoir et gérer les alertes techniques" },
    { name: "Configuration matérielle", description: "Paramétrer les équipements" },
  ],
  // user: [
  //   { name: "Consultation", description: "Consulter les informations auxquelles l'accès est autorisé" },
  // ],
};
