
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

const NotFound = () => {
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold text-primary">404</h1>
        <div className="space-y-2">
          <p className="text-xl font-medium">Page non trouvée</p>
          <p className="text-gray-500">
            La page que vous recherchez n'existe pas ou a été déplacée.
          </p>
        </div>
        <div className="pt-4">
          <Button asChild>
            <Link to={isAuthenticated ? "/dashboard" : "/login"}>
              {isAuthenticated ? "Retour au tableau de bord" : "Retour à la connexion"}
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
