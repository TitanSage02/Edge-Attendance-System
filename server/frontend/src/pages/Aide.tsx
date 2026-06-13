import { useState, useEffect } from "react";
import MainLayout from "../components/layout/MainLayout";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Search, Mail, ChevronRight, PanelLeftOpen, HelpCircle } from "lucide-react";

// Interface pour les questions fréquentes
interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
}

// Interface pour les catégories d'aide
interface HelpCategory {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
}

// Données mock pour les FAQs
const faqs: FAQ[] = [
  {
    id: "faq1",
    question: "Comment puis-je ajouter un nouvel apprenant ?",
    answer: "Pour ajouter un nouvel apprenant, accédez à la page 'Apprenants' et cliquez sur le bouton 'Ajouter un apprenant' en haut à droite. Remplissez ensuite le formulaire avec les informations requises et cliquez sur 'Ajouter'.",
    category: "apprenants"
  },
  {
    id: "faq2",
    question: "Comment puis-je enregistrer les présences manuellement ?",
    answer: "Pour enregistrer les présences manuellement, accédez à la page 'Présences', sélectionnez la date et la classe concernée, puis utilisez les cases à cocher pour marquer les présences ou les absences. N'oubliez pas de cliquer sur 'Enregistrer' pour sauvegarder vos modifications.",
    category: "presences"
  },
  {
    id: "faq3",
    question: "Que faire si un module est hors ligne ?",
    answer: "Si un module est hors ligne, vérifiez d'abord sa connexion physique et son alimentation. Ensuite, accédez à la page 'Modules' pour tenter un redémarrage à distance. Si le problème persiste, contactez le support technique via la section 'Contact' de la page d'aide.",
    category: "modules"
  },
  {
    id: "faq4",
    question: "Comment puis-je exporter les données de présence ?",
    answer: "Pour exporter les données de présence, accédez à la page 'Présences', appliquez les filtres souhaités (date, classe, etc.), puis cliquez sur le bouton 'Exporter' en haut à droite. Vous pouvez choisir d'exporter au format CSV ou Excel.",
    category: "presences"
  },
  {
    id: "faq5",
    question: "Comment modifier les informations d'un apprenant ?",
    answer: "Pour modifier les informations d'un apprenant, accédez à la page 'Apprenants', trouvez l'apprenant concerné dans la liste, puis cliquez sur l'icône d'édition dans la colonne 'Actions'. Mettez à jour les informations dans le formulaire qui s'affiche et cliquez sur 'Enregistrer'.",
    category: "apprenants"
  },
  {
    id: "faq6",
    question: "Comment puis-je configurer un nouveau module ?",
    answer: "Pour configurer un nouveau module, accédez à la page 'Modules', cliquez sur 'Ajouter un module', remplissez les informations requises comme l'ID, le nom, le type et l'emplacement. Ensuite, cliquez sur 'Ajouter' pour finaliser l'ajout. Le module sera alors visible dans la liste des modules.",
    category: "modules"
  },
  {
    id: "faq7",
    question: "Comment gérer les alertes ?",
    answer: "Pour gérer les alertes, accédez à la page 'Alertes'. Vous pouvez filtrer les alertes par type, sévérité et statut. Pour acquitter une alerte, cliquez sur le bouton 'Acquitter'. Pour archiver une alerte, cliquez sur le bouton 'Archiver'. Les alertes archivées sont accessibles via l'onglet 'Archives'.",
    category: "alertes"
  },
  {
    id: "faq8",
    question: "Comment puis-je modifier mon mot de passe ?",
    answer: "Pour modifier votre mot de passe, accédez à la page 'Mon Profil' en cliquant sur votre nom dans le coin supérieur droit, puis cliquez sur 'Modifier le mot de passe'. Entrez votre mot de passe actuel, puis votre nouveau mot de passe et confirmez-le.",
    category: "compte"
  },
  {
    id: "faq9",
    question: "Comment utiliser le chatbot d'aide ?",
    answer: "Le chatbot d'aide est disponible en bas à droite de l'écran. Cliquez sur l'icône du chatbot pour l'ouvrir, puis posez votre question dans la zone de texte. Le chatbot vous fournira des réponses en temps réel pour vous aider à naviguer et à utiliser la plateforme.",
    category: "general"
  },
  {
    id: "faq10",
    question: "Comment puis-je consulter les journaux d'activité ?",
    answer: "Pour consulter les journaux d'activité, accédez à la page 'Journal d'activité'. Vous pouvez filtrer les journaux par date, type d'action, niveau d'importance et utilisateur. Chaque entrée du journal contient des détails sur l'action effectuée, l'utilisateur qui l'a réalisée et la date et l'heure.",
    category: "logs"
  }
];

// Catégories d'aide
const categories: HelpCategory[] = [
  {
    id: "general",
    name: "Général",
    icon: <HelpCircle className="h-5 w-5" />,
    description: "Informations générales sur l'application"
  },
  {
    id: "apprenants",
    name: "Apprenants",
    icon: <PanelLeftOpen className="h-5 w-5" />,
    description: "Gestion des apprenants"
  },
  {
    id: "presences",
    name: "Présences",
    icon: <ChevronRight className="h-5 w-5" />,
    description: "Gestion des présences"
  },
  {
    id: "modules",
    name: "Modules",
    icon: <ChevronRight className="h-5 w-5" />,
    description: "Configuration et gestion des modules"
  },
  {
    id: "alertes",
    name: "Alertes",
    icon: <ChevronRight className="h-5 w-5" />,
    description: "Gestion des alertes"
  },
  {
    id: "logs",
    name: "Journal d'activité",
    icon: <ChevronRight className="h-5 w-5" />,
    description: "Consultation des journaux"
  },
  {
    id: "compte",
    name: "Compte utilisateur",
    icon: <ChevronRight className="h-5 w-5" />,
    description: "Gestion du compte utilisateur"
  }
];

const Aide = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [filteredFAQs, setFilteredFAQs] = useState<FAQ[]>(faqs);
  
  // Effet pour filtrer les FAQs en temps réel
  useEffect(() => {
    const results = faqs.filter(faq => {
      const matchesSearch = searchTerm === "" || 
        faq.question.toLowerCase().includes(searchTerm.toLowerCase()) || 
        faq.answer.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCategory = selectedCategory === null || faq.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
    
    setFilteredFAQs(results);
  }, [searchTerm, selectedCategory]);
  
  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(prev => prev === categoryId ? null : categoryId);
  };
  
  return (
    <MainLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight text-[#1f3d7a]">Centre d'aide</h1>
        
        {/* Section de recherche */}
        <Card className="bg-white">
          <CardContent className="pt-6">
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" />
                <Input
                  placeholder="Recherchez une question ou un sujet..."
                  className="pl-10"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Grille des catégories */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.map((category) => (
            <Card 
              key={category.id}
              className={`bg-white cursor-pointer transition-all hover:shadow-md ${selectedCategory === category.id ? 'ring-2 ring-[#1f3d7a]' : ''}`}
              onClick={() => handleCategorySelect(category.id)}
            >
              <CardContent className="p-4 flex flex-col items-center text-center">
                <div className={`rounded-full p-2 ${selectedCategory === category.id ? 'bg-[#1f3d7a] text-white' : 'bg-blue-100 text-[#1f3d7a]'} mb-2`}>
                  {category.icon}
                </div>
                <h3 className="font-medium text-sm mb-1">{category.name}</h3>
                <p className="text-xs text-gray-500">{category.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {/* FAQs */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-lg text-[#1f3d7a]">Questions fréquentes</CardTitle>
                <CardDescription>
                  {selectedCategory ? 
                    `Questions fréquentes sur ${categories.find(c => c.id === selectedCategory)?.name.toLowerCase() || ''}` : 
                    "Les questions les plus posées par nos utilisateurs"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {filteredFAQs.length > 0 ? (
                  <Accordion type="single" collapsible className="w-full">
                    {filteredFAQs.map((faq) => (
                      <AccordionItem key={faq.id} value={faq.id}>
                        <AccordionTrigger className="text-left">
                          {faq.question}
                        </AccordionTrigger>
                        <AccordionContent className="text-gray-600">
                          {faq.answer}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Aucun résultat trouvé pour votre recherche.</p>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setSearchTerm("");
                        setSelectedCategory(null);
                      }}
                      className="mt-4"
                    >
                      Réinitialiser les filtres
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          
          {/* Contact */}
          <div>
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-lg text-[#1f3d7a]">Nous contacter</CardTitle>
                <CardDescription>
                  Besoin d'une aide personnalisée ?
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center text-center">
                <div className="rounded-full bg-blue-100 p-4 mb-4">
                  <Mail className="h-6 w-6 text-[#1f3d7a]" />
                </div>
                <h3 className="text-lg font-medium mb-2">Support technique</h3>
                <p className="text-gray-500 mb-4">
                  Notre équipe est disponible pour vous aider avec tous vos problèmes techniques.
                </p>
                <Button className="w-full bg-[#1f3d7a] hover:bg-[#162c58]">
                  Contacter le support
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Aide;
