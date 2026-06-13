
import MainLayout from "../components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollText, FileText, AlertCircle, Gavel, ShieldCheck, HelpCircle } from "lucide-react";

const Conditions = () => {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center mb-2">
            <ScrollText className="h-6 w-6 mr-2 text-[#1f3d7a]" />
            <h1 className="text-2xl font-bold">Conditions d'utilisation</h1>
          </div>
          <p className="text-gray-500">
            Veuillez lire attentivement ces conditions d'utilisation avant d'utiliser la plateforme Edge Attendance System.
          </p>
        </div>
        
        <div className="space-y-8">
          {/* Introduction */}
          <Card className="bg-white">
            <CardHeader>
              <CardTitle>Introduction</CardTitle>
              <CardDescription>
                Dernière mise à jour : 01 juin 2025
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm">
              <p>
                Bienvenue sur Edge Attendance System, la plateforme de gestion des présences du Centre de Recherche d'Étude et de Créativité (CREC), Bénin. 
                En accédant à cette plateforme, vous acceptez d'être lié par ces conditions d'utilisation, 
                notre politique de confidentialité et toutes les lois et réglementations applicables. Si vous n'acceptez pas 
                ces conditions, veuillez ne pas utiliser cette plateforme.
              </p>
            </CardContent>
          </Card>
          
          {/* Accès à la plateforme */}
          <div className="space-y-4">
            <div className="flex items-center">
              <ShieldCheck className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Accès à la plateforme</h2>
            </div>
            
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-base">Comptes utilisateurs</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p>
                  L'accès à Edge Attendance System est réservé aux utilisateurs autorisés disposant d'un compte valide. 
                  Chaque utilisateur est responsable de la confidentialité de son identifiant et de son mot de passe. 
                  Vous êtes entièrement responsable de toutes les activités effectuées sous votre compte.
                </p>
                <p className="mt-3">
                  Vous devez immédiatement informer le CREC de toute utilisation non autorisée de votre compte 
                  ou de toute autre violation de sécurité dont vous avez connaissance.
                </p>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-base">Niveaux d'accès</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p>
                  La plateforme propose différents niveaux d'accès en fonction du rôle de l'utilisateur :
                </p>                
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Administrateur : gestion des utilisateurs, gestion des modules, accès aux logs et paramètres système</li>
                  <li>Responsable pédagogique : gestion des apprenants, suivi des présences et génération de rapports</li>
                  <li>Technicien : maintenance des modules, gestion des alertes techniques et configuration matérielle</li>
                </ul>
                <p className="mt-3">
                  Toute tentative d'accéder à des fonctionnalités au-delà de votre niveau d'autorisation 
                  est strictement interdite et pourrait entraîner la suspension de votre compte.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Utilisation de la plateforme */}
          <div className="space-y-4">
            <div className="flex items-center">
              <FileText className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Utilisation de la plateforme</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>En utilisant Edge Attendance System, vous vous engagez à :</p>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Utiliser la plateforme uniquement aux fins prévues de gestion des présences</li>
                  <li>Ne pas tenter de contourner les mesures de sécurité en place</li>
                  <li>Ne pas interférer avec le fonctionnement normal de la plateforme</li>
                  <li>Ne pas utiliser de robots, spiders, scrapers ou autres technologies automatisées</li>
                  <li>Ne pas collecter ou stocker des données personnelles d'autres utilisateurs</li>
                  <li>Ne pas transmettre de virus, malwares ou autres codes malveillants</li>
                  <li>Respecter la confidentialité des données auxquelles vous avez accès</li>
                </ul>
              </CardContent>
            </Card>
            
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-base">Données biométriques</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p>
                  La plateforme Edge Attendance System utilise des technologies de reconnaissance faciale pour 
                  l'identification des apprenants. Cette fonctionnalité est soumise à un consentement 
                  explicite préalable des personnes concernées.
                </p>
                <p className="mt-3">
                  En tant qu'utilisateur du système, vous devez vous assurer que tout traitement de 
                  données biométriques est conforme à la réglementation en vigueur et que les consentements 
                  nécessaires ont été obtenus.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Propriété intellectuelle */}
          <div className="space-y-4">
            <div className="flex items-center">
              <Gavel className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Propriété intellectuelle</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>
                  La plateforme Edge Attendance System, y compris son contenu, ses fonctionnalités et son interface, 
                  est la propriété exclusive du Centre de Recherche d'Étude et de Créativité (CREC), Bénin et est protégée par 
                  les lois sur la propriété intellectuelle.
                </p>
                <p className="mt-3">
                  Aucun élément de cette plateforme ne peut être reproduit, modifié, distribué ou exploité 
                  sans l'autorisation écrite préalable du CREC.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Limitation de responsabilité */}
          <div className="space-y-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Limitation de responsabilité</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>
                  Le CREC s'efforce de maintenir la plateforme en état de fonctionnement optimal, mais ne peut 
                  garantir qu'elle sera disponible sans interruption ni erreur. La plateforme est fournie "telle quelle" 
                  et "selon disponibilité".
                </p>
                <p className="mt-3">
                  Le CREC ne sera pas responsable des dommages directs, indirects, accessoires, consécutifs ou punitifs 
                  résultant de votre accès ou de votre utilisation de la plateforme, ou de votre incapacité à y accéder 
                  ou à l'utiliser.
                </p>
              </CardContent>
            </Card>
          </div>
          
          {/* Modification des conditions */}
          <div className="space-y-4">
            <div className="flex items-center">
              <HelpCircle className="h-5 w-5 mr-2 text-[#1f3d7a]" />
              <h2 className="text-xl font-bold">Modifications des conditions</h2>
            </div>
            
            <Card className="bg-white">
              <CardContent className="text-sm pt-6">
                <p>
                  Le CREC se réserve le droit de modifier ces conditions d'utilisation à tout moment. Les modifications 
                  prendront effet dès leur publication sur la plateforme. Nous vous encourageons à consulter régulièrement 
                  ces conditions pour vous tenir informé des mises à jour.
                </p>
                <p className="mt-3">
                  Votre utilisation continue de la plateforme après la publication des modifications constituera 
                  votre acceptation de ces modifications.
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
                Si vous avez des questions concernant ces conditions d'utilisation, veuillez nous contacter à l'adresse suivante :
              </p>
              <p className="mt-3 font-medium">
                Centre de Recherche d'Étude et de Créativité (CREC)<br />
                Service Juridique<br />
                Bénin<br />
                Email : legal@example.org
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
};

export default Conditions;
