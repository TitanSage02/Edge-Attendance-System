import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

interface AlertsProps {
  total: number;
}

/**
 * Composant affichant les alertes actives sur le tableau de bord
 */
export const DashboardAlerts = ({ total }: AlertsProps) => {
  return (
    <Link to="/alertes">
      <Card className="bg-white hover:shadow-md transition-all duration-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">
            <div className="flex justify-between items-center">
              <span className="text-[#1f3d7a]">Alertes actives</span>
              <AlertTriangle className="h-4 w-4 text-[#ea384c]" />
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-[#1f3d7a]">{total}</div>
          {/* {critical && critical > 0 && (
            <div className="text-sm text-red-600 mt-1">
              Dont {critical} critique{critical > 1 ? 's' : ''}
            </div>
          )} */}
        </CardContent>
      </Card>
    </Link>
  );
};

export default DashboardAlerts;
