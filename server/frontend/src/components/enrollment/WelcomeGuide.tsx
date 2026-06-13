import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Camera, Users, Settings, Save, Keyboard } from "lucide-react";

interface WelcomeGuideProps {
  isOpen: boolean;
  onClose: () => void;
}

const WelcomeGuide: React.FC<WelcomeGuideProps> = ({ isOpen, onClose }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">        
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2 text-lg">
            <Camera className="h-5 w-5 text-blue-600" />
            <span>Guide d'enrôlement</span>
          </DialogTitle>
          <DialogDescription className="text-sm">
            Suivez ces étapes pour enrôler vos apprenants.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">          
          {/* Étapes du processus */}
          <div className="space-y-3">
            <h3 className="font-semibold text-base flex items-center space-x-2">
              <Users className="h-4 w-4 text-orange-500" />
              <span>Processus d'enrôlement</span>
            </h3>
            
            <div className="space-y-2">
              <div className="flex items-start space-x-3">
                <Badge className="bg-blue-100 text-blue-700 px-2 py-1 text-sm">1</Badge>
                <div>
                  <p className="font-medium">Sélectionner la classe</p>
                  <p className="text-sm text-gray-600">Choisissez d'abord la classe pour filtrer les apprenants</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Badge className="bg-blue-100 text-blue-700 px-2 py-1 text-sm">2</Badge>
                <div>
                  <p className="font-medium">Choisir l'apprenant</p>
                  <p className="text-sm text-gray-600">Sélectionnez l'apprenant à enrôler dans la liste filtrée</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Badge className="bg-blue-100 text-blue-700 px-2 py-1 text-sm">3</Badge>
                <div>
                  <p className="font-medium">Vérifier les informations</p>
                  <p className="text-sm text-gray-600">Modifiez si nécessaire les informations de l'apprenant (nom, prénom, carte RFID)</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Badge className="bg-blue-100 text-blue-700 px-2 py-1 text-sm">4</Badge>
                <div>
                  <p className="font-medium">Capturer 6 photos</p>
                  <p className="text-sm text-gray-600">Prenez 6 photos de l'apprenant sous différents angles</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Badge className="bg-blue-100 text-blue-700 px-2 py-1 text-sm">5</Badge>
                <div>
                  <p className="font-medium">Sauvegarder l'enrôlement</p>
                  <p className="text-sm text-gray-600">Validez l'enrôlement pour passer à l'apprenant suivant</p>
                </div>
              </div>
            </div>
          </div>

          {/* Conseils de capture */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <Camera className="h-5 w-5 text-green-500" />
              <span>Conseils pour de bonnes captures</span>
            </h3>
            
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <ul className="space-y-2 text-sm">
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Assurez-vous que le visage est bien éclairé</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Regardez directement la caméra</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Variez légèrement les angles entre les captures</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Évitez les ombres sur le visage</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Raccourcis clavier */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <Keyboard className="h-5 w-5 text-purple-500" />
              <span>Raccourcis clavier</span>
            </h3>
            
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <div className="grid grid-cols-2 gap-3 text-sm">
                
                <div className="flex justify-between">
                  <span>Capturer une photo:</span>
                  <Badge variant="outline" className="bg-white">Espace</Badge>
                </div>
                
                <div className="flex justify-between">
                  <span>Sauvegarder:</span>
                  <Badge variant="outline" className="bg-white">Entrée</Badge>
                </div>
                
                <div className="flex justify-between">
                  <span>Efface la dernière photo:</span>
                  <Badge variant="outline" className="bg-white">Backspace</Badge>
                </div>
                
                <div className="flex justify-between">
                  <span>Navigation:</span>
                  <Badge variant="outline" className="bg-white">← →</Badge>
                </div>

              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex items-center space-x-2"
            >
              <Settings className="h-4 w-4" />
              <span>Aide (F1)</span>
            </Button>
            
            <Button
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
            >
              <Save className="h-4 w-4" />
              <span>Commencer l'enrôlement</span>
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WelcomeGuide;
