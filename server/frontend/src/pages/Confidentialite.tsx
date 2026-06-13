
import MainLayout from "../components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Lock, Database, Eye, Files, Clock } from "lucide-react";

const Confidentialite = () => {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center mb-2">
            <Shield className="h-6 w-6 mr-2 text-[#1f3d7a]" />
            <h1 className="text-2xl font-bold">Politique de confidentialité</h1>
          </div>
          <p className="text-gray-500">
            Cette politique de confidentialité décrit comment Edge Attendance System collecte, utilise et protège vos données.
          </p>
        </div>
        
        <div className="space-y-8">
          {/* Introduction */}
          <Card className="bg-white">
            <CardHeader>
              <CardTitle>Introduction</CardTitle>
              <CardDescription>
                Dernière mise à jour : 15 avril 2023
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm">
              <p>
                Le Centre de Recherche d'Étude et de Créativité (CREC), Bénin, s'engage à protéger la vie privée des utilisateurs
                de sa plateforme de gestion des présences. Cette politique de confidentialité explique quelles informations
                nous collectons, comment nous les utilisons et comment nous les protégeons.
              </p>
              <p className="mt-3">
                En utilisant la plateforme Edge Attendance System, vous acceptez les pratiques décrites dans cette politique.
                Si vous n'acceptez pas cette politique, veuillez ne pas utiliser notre plateforme.
              </p>
            </CardContent>
          </Card>
          
          {/* Collecte des données */}
          <div className="space-y-4">
            <div className="flex items-center">
              <Database className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Collecte des données</h2>
            </div>
            
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-base">Informations personnelles</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p>Nous collectons les informations suivantes :</p>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Nom et prénom</li>
                  <li>Adresse email professionnelle</li>
                  <li>Statut au sein de l'établissement</li>
                  <li>Identifiants uniques pour l'authentification</li>
                  <li>Adresse IP et informations de connexion</li>
                  <li>Pour les apprenants : RFID, données biométriques (empreintes faciales)</li>
                </ul>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-base">Données de présence</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p>
                  Pour les apprenants, nous collectons les données relatives à leurs présences et absences,
                  incluant les heures d'entrée et de sortie, les modules fréquentés et les méthodes
                  d'identification utilisées (RFID, reconnaissance faciale, saisie manuelle).
                </p>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-base">Données techniques</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p>
                  Nous collectons des informations techniques sur votre connexion, votre appareil
                  et votre utilisation de la plateforme à des fins de sécurité et d'amélioration
                  de nos services.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Utilisation des données */}
          <div className="space-y-4">
            <div className="flex items-center">
              <Eye className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Utilisation des données</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>Nous utilisons vos données personnelles pour les finalités suivantes :</p>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Gérer l'authentification et la sécurité de votre compte</li>
                  <li>Permettre le suivi des présences des apprenants</li>
                  <li>Générer des rapports statistiques anonymisés</li>
                  <li>Améliorer notre plateforme et son fonctionnement</li>
                  <li>Assurer la sécurité et la maintenance de nos systèmes</li>
                  <li>Respecter nos obligations légales et réglementaires</li>
                </ul>
              </CardContent>
            </Card>
          </div>
          
          {/* Conservation des données */}
          <div className="space-y-4">
            <div className="flex items-center">
              <Clock className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Conservation des données</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>
                  Nous conservons vos données personnelles aussi longtemps que nécessaire pour
                  atteindre les finalités pour lesquelles nous les avons collectées, notamment
                  pour satisfaire aux exigences légales et réglementaires.
                </p>
                <p className="mt-3">
                  Les données de présence sont conservées pendant la durée de la formation de l'apprenant
                  et jusqu'à trois ans après la fin de sa formation.
                </p>
                <p className="mt-3">
                  Les logs de connexion et de sécurité sont conservés pendant une durée maximale d'un an.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Protection des données */}
          <div className="space-y-4">
            <div className="flex items-center">
              <Lock className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Protection des données</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>
                  Nous mettons en œuvre des mesures de sécurité techniques et organisationnelles
                  appropriées pour protéger vos données personnelles contre les accès non autorisés,
                  la divulgation, l'altération ou la destruction.
                </p>
                <p className="mt-3">
                  Ces mesures comprennent le chiffrement des données, l'authentification à deux facteurs,
                  des pare-feu, des audits de sécurité réguliers et des politiques strictes d'accès aux données.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Droits des utilisateurs */}
          <div className="space-y-4">
            <div className="flex items-center">
              <Files className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Vos droits</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>Conformément aux lois sur la protection des données, vous disposez des droits suivants :</p>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Droit d'accès à vos données personnelles</li>
                  <li>Droit de rectification des données inexactes</li>
                  <li>Droit à l'effacement (droit à l'oubli)</li>
                  <li>Droit à la limitation du traitement</li>
                  <li>Droit à la portabilité des données</li>
                  <li>Droit d'opposition au traitement</li>
                </ul>
                <p className="mt-3">
                  Pour exercer ces droits, veuillez contacter notre délégué à la protection des données
                  à l'adresse suivante : dpo@example.org
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Contact */}
          <Card className="bg-white">
            <CardHeader>
              <CardTitle>Contact</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <p>
                Si vous avez des questions concernant cette politique de confidentialité ou nos pratiques
                en matière de protection des données, veuillez nous contacter à l'adresse suivante :
              </p>
              <p className="mt-3 font-medium">
                Centre de Recherche d'Étude et de Créativité (CREC)<br />
                Service Protection des Données<br />
                Bénin<br />
                Email : privacy@example.org
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
};

export default Confidentialite;
