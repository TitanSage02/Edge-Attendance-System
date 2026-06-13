import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Camera, CheckCircle, AlertCircle } from "lucide-react";

interface CaptureGuideProps {
  capturedCount: number;
  isCapturing: boolean;
}

const CaptureGuide: React.FC<CaptureGuideProps> = ({ capturedCount, isCapturing }) => {
  const guidelines = [
    {
      id: 1,
      text: "Regardez directement la caméra",
      icon: Camera,
      completed: capturedCount >= 1,
    },
    {
      id: 2,
      text: "Gardez votre visage dans le cadre",
      icon: Camera,
      completed: capturedCount >= 2,
    },
    {
      id: 3,
      text: "Évitez les mouvements brusques",
      icon: Camera,
      completed: capturedCount >= 3,
    },
    {
      id: 4,
      text: "Assurez-vous d'un bon éclairage",
      icon: Camera,
      completed: capturedCount >= 4,
    }
  ];

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardContent className="pt-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-blue-800">Guide de capture</h4>
          <Badge 
            variant={capturedCount === 5 ? "default" : "secondary"}
            className={capturedCount === 5 ? "bg-green-500" : ""}
          >
            {capturedCount}/5 réalisées
          </Badge>
        </div>
        
        <div className="space-y-2">
          {guidelines.map((guideline) => {
            const Icon = guideline.completed ? CheckCircle : guideline.icon;
            return (
              <div
                key={guideline.id}
                className={`flex items-center space-x-2 text-sm transition-colors ${
                  guideline.completed 
                    ? "text-green-700" 
                    : "text-blue-600"
                }`}
              >
                <Icon 
                  className={`h-4 w-4 ${
                    guideline.completed ? "text-green-600" : "text-blue-500"
                  }`} 
                />
                <span className={guideline.completed ? "line-through" : ""}>
                  {guideline.text}
                </span>
              </div>
            );
          })}
        </div>

        {isCapturing && (
          <div className="mt-3 p-2 bg-orange-100 rounded-md border border-orange-200">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-orange-600 animate-pulse" />
              <span className="text-xs text-orange-700 font-medium">
                Capture en cours... Restez immobile
              </span>
            </div>
          </div>
        )}

        {capturedCount === 5 && (
          <div className="mt-3 p-2 bg-green-100 rounded-md border border-green-200">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-xs text-green-700 font-medium">
                Toutes les captures sont terminées !
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CaptureGuide;
