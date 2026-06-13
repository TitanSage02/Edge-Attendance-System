# Documentation Technique et Utilisateur de la Plateforme Edge Attendance System

## Table des matières
1. [Introduction](#introduction)
2. [Architecture générale](#architecture-générale)
3. [Fonctionnalités principales](#fonctionnalités-principales)
4. [Modèles de données](#modèles-de-données)
5. [Interfaces utilisateur](#interfaces-utilisateur)
6. [Gestion des présences](#gestion-des-présences)
7. [Gestion des apprenants](#gestion-des-apprenants)
8. [Gestion des modules](#gestion-des-modules)
9. [Système d'authentification et sécurité](#système-dauthentification-et-sécurité)
10. [Système de chatbot](#système-de-chatbot)
11. [FAQ et résolution des problèmes](#faq-et-résolution-des-problèmes)
12. [Guides pour les administrateurs](#guides-pour-les-administrateurs)

## Introduction

La plateforme Edge Attendance System est un système de gestion de présence conçu pour les établissements éducatifs. Elle permet de suivre la présence des apprenants dans différentes classes à travers des modules physiques de détection (reconnaissance faciale et RFID), ainsi qu'une saisie manuelle. Le système offre une interface web moderne, des tableaux de bord analytiques, et diverses fonctionnalités d'administration.

**Objectifs de la plateforme:**
- Automatiser la prise de présence des apprenants
- Fournir des statistiques précises sur la présence
- Permettre une gestion efficace des apprenants et des modules
- Offrir une interface utilisateur conviviale et responsive
- Assurer la sécurité des données sensibles

## Architecture générale

La plateforme Edge Attendance System est construite sur une architecture moderne client-serveur:

### Backend (API)
- **Technologie**: Python avec FastAPI
- **Base de données**: PostgreSQL
- **Communication IoT**: MQTT pour les modules de détection
- **Sécurité**: JWT pour l'authentification, chiffrement des données sensibles

### Frontend
- **Technologie**: React avec TypeScript
- **UI Framework**: Composants personnalisés avec Tailwind CSS
- **Gestion d'état**: React Query pour les appels API
- **Routage**: React Router pour la navigation

### Système de chatbot
- **Type**: Système RAG (Retrieval-Augmented Generation)
- **Base de vecteurs**: VectorStore pour stocker les embeddings
- **Modèle**: Gemini pour les embeddings et les réponses du chatbot
- **Sources de données**: Journal d'activité, documentation, et FAQ

## Fonctionnalités principales

### Gestion des présences
- Enregistrement automatique par reconnaissance faciale
- Enregistrement automatique par badge RFID
- Saisie manuelle des présences
- Visualisation des statistiques de présence
- Exportation des données au format CSV ou Excel

### Gestion des apprenants
- Ajout, modification et suppression d'apprenants
- Enrôlement facial des apprenants
- Enrôlement des badges RFID
- Consultation de l'historique de présence individuel

### Gestion des modules
- Configuration des modules de détection
- Surveillance de l'état des modules (online, offline, warning)
- Affectation des modules à des emplacements

### Tableau de bord
- Vue d'ensemble des statistiques de présence
- Alertes pour les modules hors ligne ou en erreur
- Graphiques de tendance de présence

### Système de chatbot d'assistance
- Assistant IA pour répondre aux questions des utilisateurs
- Base de connaissances alimentée par la documentation et les logs

## Modèles de données

### Apprenant (Student)
- **id**: Identifiant unique (chaîne)
- **firstName**: Prénom
- **lastName**: Nom de famille
- **rfidUid**: Identifiant du badge RFID (chiffré)
- **embeddings**: Vecteurs d'encodage facial
- **classGroup**: Groupe/Classe
- **promotion**: Promotion/Année
- **faceEnrolled**: Statut d'enrôlement facial
- **rfidEnrolled**: Statut d'enrôlement RFID

### Présence (Presence)
- **id**: Identifiant unique
- **student_id**: Référence à l'apprenant
- **status**: Statut de présence (vrai pour présent, faux pour absent)
- **module_uid**: Module qui a enregistré la présence
- **timestamp**: Horodatage de l'enregistrement

### Module (Module)
- **uid**: Identifiant unique
- **name**: Nom du module
- **description**: Description du module
- **emplacement**: Lieu d'installation
- **faceChecked**: Activation de la vérification faciale
- **rfidChecked**: Activation de la vérification RFID
- **status**: État du module (online, idle, offline, warning)

### Utilisateur (User)
- **id**: Identifiant unique
- **email**: Adresse email
- **firstName**: Prénom
- **lastName**: Nom de famille
- **role**: Rôle (admin, professeur, etc.)
- **password_hash**: Mot de passe haché

## Interfaces utilisateur

### Pages principales
1. **Tableau de bord** `/dashboard`: Vue d'ensemble avec statistiques et graphiques
2. **Apprenants** `/apprenants`: Gestion des apprenants (liste, ajout, modification, suppression)
3. **Enrôlement** `/enrollment`: Interface d'enrôlement facial des apprenants
4. **Présences** `/presences`: Gestion et visualisation des présences
5. **Modules** `/modules`: Configuration et surveillance des modules de détection
6. **Alertes** `/alertes`: Centre de notification pour les alertes système
7. **Paramètres** `/parametres`: Configuration générale du système
8. **Gestion des utilisateurs** `/admin-utilisateurs`: Administration des utilisateurs (admin uniquement)
9. **Profil** `/profile`: Gestion du profil utilisateur
10. **Aide** `/aide`: Centre d'aide avec FAQ et documentation

### Navigation
- **Sidebar**: Navigation principale avec accès aux fonctionnalités selon les droits
- **TopBar**: Barre supérieure avec profil utilisateur, notifications et recherche
- **Chatbot**: Assistant IA accessible depuis toutes les pages

## Gestion des présences

### Méthodes d'enregistrement
1. **Automatique par reconnaissance faciale**:
   - Les modules équipés de caméras détectent les visages
   - Comparaison avec les embeddings enregistrés
   - Enregistrement automatique de la présence

2. **Automatique par badge RFID**:
   - Les modules équipés de lecteurs RFID détectent les badges
   - Vérification de l'UID du badge avec la base de données
   - Enregistrement automatique de la présence

3. **Manuelle**:
   - Interface web pour les enseignants et administrateurs
   - Sélection de la date, classe et apprenants
   - Enregistrement manuel des présences et absences

### Logique d'entrée/sortie
- Si un apprenant passe un même module une deuxième fois après au moins 2 minutes, le système considère que c'est une sortie
- L'heure d'entrée et de sortie est enregistrée pour des statistiques précises

### Exportation des données
- Format CSV ou Excel
- Filtrage par période, classe, ou apprenant
- Données complètes incluant les heures d'entrée et sortie

## Gestion des apprenants

### Ajout d'un nouvel apprenant
1. Accéder à la page **Apprenants**
2. Cliquer sur le bouton **Ajouter un apprenant**
3. Remplir le formulaire avec les informations requises:
   - Identifiant
   - Prénom et nom
   - Classe/groupe
   - Promotion

### Enrôlement facial
1. Accéder à la page **Apprenants**
2. Sélectionner un apprenant
3. Cliquer sur **Enrôlement facial**
4. Suivre les instructions pour capturer le visage de l'apprenant
5. Le système génère et stocke les embeddings faciaux de manière sécurisée

### Enrôlement RFID
1. Accéder à la page **Apprenants**
2. Sélectionner un apprenant
3. Cliquer sur **Enrôlement RFID**
4. Passer le badge RFID sur un module en mode enrôlement
5. Le système associe l'UID du badge à l'apprenant de manière chiffrée

### Modification des informations
1. Accéder à la page **Apprenants**
2. Trouver l'apprenant concerné dans la liste
3. Cliquer sur l'icône d'édition dans la colonne **Actions**
4. Mettre à jour les informations dans le formulaire
5. Cliquer sur **Enregistrer**

## Gestion des modules

### Configuration d'un nouveau module
1. Accéder à la page **Modules**
2. Cliquer sur **Ajouter un module**
3. Remplir le formulaire:
   - ID unique
   - Nom et description
   - Emplacement
   - Configuration des méthodes de détection (faciale, RFID)
4. Cliquer sur **Ajouter**

### Surveillance des modules
- Statut en temps réel (online, offline, idle, warning)
- Dernière connexion
- Statistiques de détection
- Alertes automatiques en cas de problème

### Maintenance
- Option de redémarrage à distance
- Mise à jour de la configuration
- Désactivation temporaire

## Système d'authentification et sécurité

### Authentification
- Système basé sur JWT (JSON Web Tokens)
- Sessions avec expiration
- Contrôle d'accès basé sur les rôles

### Sécurité des données sensibles
- Chiffrement des identifiants RFID
- Stockage sécurisé des embeddings faciaux
- Conformité RGPD pour les données personnelles

### Contrôle d'accès
- **Admin**: Accès complet à toutes les fonctionnalités
- **Professeur**: Accès à la gestion des présences et visualisation des données
- **Observateur**: Accès en lecture seule aux données de présence

## Système de chatbot

### Architecture RAG
- **Retrieval**: Recherche dans la base de connaissances
- **Augmentation**: Enrichissement du contexte avec les données pertinentes
- **Generation**: Génération de réponses précises et contextuelles

### Sources de données
- Documentation système
- FAQ prédéfinies
- Journaux d'activité traités

### Fonctionnalités
- Réponse aux questions fréquentes
- Assistance à la navigation dans la plateforme
- Aide au diagnostic des problèmes courants
- Suggestions basées sur le contexte d'utilisation

### Surveillance et amélioration
- Analyse des requêtes fréquentes
- Mise à jour automatique de la base de connaissances
- Surveillance des logs pour enrichir les réponses

## FAQ et résolution des problèmes

### Comment puis-je ajouter un nouvel apprenant ?
Pour ajouter un nouvel apprenant, accédez à la page 'Apprenants' et cliquez sur le bouton 'Ajouter un apprenant' en haut à droite. Remplissez ensuite le formulaire avec les informations requises et cliquez sur 'Ajouter'.

### Comment puis-je enregistrer les présences manuellement ?
Pour enregistrer les présences manuellement, accédez à la page 'Présences', sélectionnez la date et la classe concernée, puis utilisez les cases à cocher pour marquer les présences ou les absences. N'oubliez pas de cliquer sur 'Enregistrer' pour sauvegarder vos modifications.

### Que faire si un module est hors ligne ?
Si un module est hors ligne, vérifiez d'abord sa connexion physique et son alimentation. Ensuite, accédez à la page 'Modules' pour tenter un redémarrage à distance. Si le problème persiste, contactez le support technique via la section 'Contact' de la page d'aide.

### Comment puis-je exporter les données de présence ?
Pour exporter les données de présence, accédez à la page 'Présences', appliquez les filtres souhaités (date, classe, etc.), puis cliquez sur le bouton 'Exporter' en haut à droite. Vous pouvez choisir d'exporter au format CSV ou Excel.

### Comment modifier les informations d'un apprenant ?
Pour modifier les informations d'un apprenant, accédez à la page 'Apprenants', trouvez l'apprenant concerné dans la liste, puis cliquez sur l'icône d'édition dans la colonne 'Actions'. Mettez à jour les informations dans le formulaire qui s'affiche et cliquez sur 'Enregistrer'.

### Comment puis-je configurer un nouveau module ?
Pour configurer un nouveau module, accédez à la page 'Modules', cliquez sur 'Ajouter un module', remplissez les informations requises comme l'ID, le nom, le type et l'emplacement. Ensuite, cliquez sur 'Ajouter' pour finaliser l'ajout. Le module sera alors visible dans la liste des modules.

### Comment gérer les alertes ?
Pour gérer les alertes, accédez à la page 'Alertes'. Vous pouvez filtrer les alertes par type, sévérité et statut. Pour acquitter une alerte, cliquez sur le bouton 'Acquitter'. Pour archiver une alerte, cliquez sur le bouton 'Archiver'. Les alertes archivées sont accessibles via l'onglet 'Archives'.

### Comment puis-je modifier mon mot de passe ?
Pour modifier votre mot de passe, accédez à la page 'Mon Profil' en cliquant sur votre nom dans le coin supérieur droit, puis cliquez sur 'Modifier le mot de passe'. Entrez votre mot de passe actuel, puis votre nouveau mot de passe et confirmez-le.

### Comment utiliser le chatbot d'aide ?
Le chatbot d'aide est disponible en bas à droite de l'écran. Cliquez sur l'icône du chatbot pour l'ouvrir, puis posez votre question dans la zone de texte. Le chatbot vous fournira des réponses en temps réel pour vous aider à naviguer et à utiliser la plateforme.

### Comment puis-je consulter les journaux d'activité ?
Pour consulter les journaux d'activité, accédez à la page 'Journal d'activité'. Vous pouvez filtrer les journaux par date, type d'action, niveau d'importance et utilisateur. Chaque entrée du journal contient des détails sur l'action effectuée, l'utilisateur qui l'a réalisée et la date et l'heure.

## Guides pour les administrateurs

### Configuration initiale du système
1. Créer le premier compte administrateur
2. Configurer les paramètres généraux du système
3. Ajouter les modules physiques
4. Créer les comptes utilisateurs

### Maintenance quotidienne
1. Vérifier l'état des modules
2. Traiter les alertes en attente
3. Vérifier les journaux d'activité
4. Exporter les données de présence si nécessaire

### Procédures de sauvegarde
1. Sauvegarde automatique de la base de données
2. Sauvegarde manuelle via l'interface d'administration
3. Exportation régulière des données

### Gestion des rôles et permissions
1. Création et assignation des rôles
2. Configuration des permissions spécifiques
3. Audit des accès utilisateurs
