import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect, useState } from "react";

interface ClassAttendance {
  name: string;
  present: number;
  absent: number;
}

interface AttendanceChartProps {
  data: ClassAttendance[];
}

/**
 * Composant de barre de progression professionnelle avec animation
 */
interface ProgressBarProps {
  className: string;
  present: number;
  total: number;
  fillPercentage: number;
  isAnimating: boolean;
}

const AttendanceProgressBar = ({ className, present, total, fillPercentage, isAnimating }: ProgressBarProps) => {
  // Déterminer la couleur selon le taux de présence
  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'from-emerald-500 to-emerald-600';
    if (percentage >= 60) return 'from-amber-500 to-amber-600';
    return 'from-red-500 to-red-600';
  };

  const getTextColor = (percentage: number) => {
    if (percentage >= 80) return 'text-emerald-600';
    if (percentage >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className="flex flex-col items-center space-y-2 sm:space-y-3 p-2 sm:p-3 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200 min-w-[100px] sm:min-w-[120px] w-full sm:w-auto">
      {/* Nom de la classe */}
      <div className="text-center w-full">
        <h4 className="text-sm font-semibold text-gray-800 truncate">{className}</h4>
        <p className="text-xs text-gray-500 mt-0.5 sm:mt-1">
          {present} / {total} élèves
        </p>
      </div>
      
      {/* Container de la barre de progression */}
      <div className="relative w-full">
        {/* Barre de fond */}
        <div className="w-full h-4 sm:h-5 bg-gray-100 rounded-lg border border-gray-200 overflow-hidden">
          {/* Barre de progression */}
          <div 
            className={`h-full bg-gradient-to-r ${getProgressColor(fillPercentage)} transition-all duration-1000 ease-out relative`}
            style={{ 
              width: isAnimating ? `${fillPercentage}%` : '0%'
            }}
          >
            {/* Effet de brillance subtil */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-20"></div>
          </div>
        </div>
        
        {/* Pourcentage centré sur la barre */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-bold text-white drop-shadow-sm">
            {Math.round(fillPercentage)}%
          </span>
        </div>
      </div>

      {/* Indicateur de statut */}
      <div className="flex items-center space-x-1.5 sm:space-x-2">
        <div 
          className={`w-1.5 sm:w-2 h-1.5 sm:h-2 rounded-full ${
            fillPercentage >= 80 ? 'bg-emerald-500' :
            fillPercentage >= 60 ? 'bg-amber-500' : 'bg-red-500'
          }`}
        />
        <span className={`text-[10px] sm:text-xs font-medium ${getTextColor(fillPercentage)}`}>
          {fillPercentage >= 80 ? 'Excellent' :
           fillPercentage >= 60 ? 'Moyen' : 'Faible'}
        </span>
      </div>
    </div>
  );
};

/**
 * Composant du graphique de présence par classe
 */
export const DashboardAttendanceChart = ({ data }: AttendanceChartProps) => {
  const [isAnimating, setIsAnimating] = useState(false);

  // Lancer l'animation au montage du composant
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsAnimating(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);
  // Transformation des données pour les barres de progression
  const progressData = data.map(cls => {
    const total = cls.present + cls.absent;
    const fillPercentage = total > 0 ? (cls.present / total) * 100 : 0;
    return {
      name: cls.name,
      present: cls.present,
      total: total,
      fillPercentage: fillPercentage
    };
  });

  // Calculer les totaux
  const totals = data.reduce((acc, cls) => ({
    présents: acc.présents + cls.present,
    absents: acc.absents + cls.absent
  }), { présents: 0, absents: 0 });

  const totalGeneral = totals.présents + totals.absents;
  const tauxPresenceGeneral = totalGeneral > 0 ? Math.round((totals.présents / totalGeneral) * 100) : 0;
  
  return (
    <Link to="/presences" className="block">
      <Card className="h-full bg-white hover:shadow-md transition-all duration-200">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg text-[#1f3d7a]">Présence du jour</CardTitle>
          <CardDescription>Taux de présence par classe</CardDescription>
        </CardHeader>
        
        <CardContent>
          {data.length === 0 ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-gray-500 text-center">
                Aucune donnée de présence disponible pour aujourd'hui.
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Statistiques générales */}
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div className="text-sm">
                  <span className="font-medium text-gray-700">Total présents: </span>
                  <span className="font-bold text-[#1f3d7a]">{totals.présents}</span>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-700">Total absents: </span>
                  <span className="font-bold text-[#ea384c]">{totals.absents}</span>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-700">Taux global: </span>
                  <span className="font-bold text-green-600">{tauxPresenceGeneral}%</span>
                </div>
              </div>              
              {/* Conteneur des barres de progression */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-3 py-3">
                {progressData.map((cls, index) => (
                  <AttendanceProgressBar
                    key={index}
                    className={cls.name}
                    present={cls.present}
                    total={cls.total}
                    fillPercentage={cls.fillPercentage}
                    isAnimating={isAnimating}
                  />
                ))}
              </div>

              {/* Légende */}
              <div className="flex justify-center items-center space-x-6 text-xs text-gray-600 pt-2">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-emerald-500 rounded"></div>
                  <span>Excellent (≥80%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-amber-500 rounded"></div>
                  <span>Moyen (60-79%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded"></div>
                  <span>Faible (&lt;60%)</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
};

export default DashboardAttendanceChart;
