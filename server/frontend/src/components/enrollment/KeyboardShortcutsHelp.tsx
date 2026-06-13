import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({ isOpen, onClose }) => {  const shortcuts = [
    {
      key: "F1",
      description: "Ouvrir cette aide",
      condition: "À tout moment",
    },
    {
      key: "Espace",
      description: "Capturer une photo",
      condition: "Quand la caméra est active",
    },
    {
      key: "Backspace",
      description: "Effacer la dernière photo capturée",
      condition: "Quand une photo est capturée",
    },
    {
      key: "Entrée",
      description: "Sauvegarder l'enrôlement",
      condition: "Quand 6 photos sont capturées",
    },
    {
      key: "← →",
      description: "Naviguer entre les apprenants",
      condition: "Navigation disponible",
    },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <span>Raccourcis clavier</span>
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Utilisez ces raccourcis pour naviguer plus rapidement dans l'interface.
          </p>
          
          {/* Note importante sur la désactivation */}
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <div className="flex items-start space-x-2">
              <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center mt-0.5">
                <span className="text-white text-xs">ℹ</span>
              </div>
              <div className="text-sm text-blue-800">
                <p className="font-medium">Mode intelligent</p>
                <p className="text-xs text-blue-600 mt-1">
                  Les raccourcis sont automatiquement désactivés lorsque vous tapez dans un champ de saisie (sauf F1).
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            {shortcuts.map((shortcut, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-1">
                  <div className="font-medium text-sm">{shortcut.description}</div>
                  <div className="text-xs text-gray-500 mt-1">{shortcut.condition}</div>
                </div>
                <Badge variant="outline" className="font-mono text-xs">
                  {shortcut.key}
                </Badge>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-500 text-center pt-2 border-t">
            💡 Astuce: Maintenez les touches pour des actions répétées
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default KeyboardShortcutsHelp;
