import { ReactNode, useState, useEffect } from "react";
import { Navigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { useIsMobile } from "@/hooks/use-mobile";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import Chatbot from "../chat/Chatbot";

interface MainLayoutProps {
  children: ReactNode;
  requiredRoles?: string[];
  forceSidebarClosed?: boolean;
}

const pageTitles: Record<string, string> = {
  '/dashboard': 'Tableau de bord',
  '/apprenants': 'Apprenants',
  '/enrollment': 'Enrôlement des visages',
  '/presences': 'Présences',
  '/modules': 'Modules',
  '/alertes': 'Alertes',
  '/parametres': 'Paramètres',
  '/admin-utilisateurs': 'Gestion des utilisateurs',
  '/profile': 'Mon Profil',
  '/confidentialite': 'Confidentialité',
  '/conditions': 'Conditions d\'utilisation',
  '/aide': 'Aide',
};

const MainLayout = ({ children, requiredRoles, forceSidebarClosed = false }: MainLayoutProps) => {
  const { isAuthenticated, loading, hasRole, user } = useAuth();
  const { error } = useUnifiedToast();
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const [pageTitle, setPageTitle] = useState('Edge Attendance System');
  // Gestion responsive de la sidebar
  useEffect(() => {
    if (forceSidebarClosed) {
      setSidebarOpen(false);
    } else if (isMobile) {
      setSidebarOpen(false);
    } else {
      setSidebarOpen(true);
    }
  }, [isMobile, forceSidebarClosed]);

  useEffect(() => {
    setPageTitle(pageTitles[location.pathname] || 'Edge Attendance System');
    document.title = `${pageTitles[location.pathname] || 'Edge Attendance System'} | Edge Attendance System`;
  }, [location.pathname]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#1f3d7a]"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) { // Si l'utilisateur n'est pas authentifié
    // Rediriger vers la page de connexion
    return <Navigate to="/login" replace />;
  }  
  
  if (requiredRoles && requiredRoles.length > 0) {   
    // Vérification des rôles plus robuste
    if (!isAuthenticated || !hasRole) {
      return <Navigate to="/login" replace />;
    }
    
    // Si l'utilisateur est authentifié mais n'a pas le rôle requis
    const userRole = typeof hasRole === 'function' && user ? user.role : null;
    // console.log('User Role:', userRole);
    // console.log('Required Roles:', requiredRoles);
    
    const hasRequiredRole = requiredRoles.some(role => {
      const hasAccess = typeof hasRole === 'function' ? hasRole(role as any) : false;
      //  console.log(`Checking role ${role}: ${hasAccess}`);
      return hasAccess;
    });
    if (!hasRequiredRole) {
      // console.log('Redirecting to dashboard due to missing role');
      error("Vous n'avez pas les permissions nécessaires pour accéder à cette page.", { title: "Accès refusé" });
      return <Navigate to="/dashboard" replace />;
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f5]">
      {/* Overlay pour mobile quand sidebar est ouverte */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Fixed sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 ${isMobile ? '' : 'z-20'}`}>
        <Sidebar 
          isOpen={sidebarOpen} 
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          isMobile={isMobile}
        />
      </div>

      {/* Main content area with fixed header */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${
        !isMobile && sidebarOpen ? 'pl-64' : !isMobile ? 'pl-20' : 'pl-0'
      }`}>
        {/* Fixed header avec z-index plus élevé */}
        <div className={`fixed top-0 right-0 z-30 transition-all duration-300 bg-white border-b ${
          !isMobile && sidebarOpen ? 'left-64' : !isMobile ? 'left-20' : 'left-0'
        }`}>
          <TopBar 
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
            pageTitle={pageTitle}
          />        
        </div>

        {/* Main content avec padding-top ajusté */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto pt-20 pb-16 px-3 sm:px-4 md:px-6">
          {children}
        </main>

        {/* Fixed footer */}
        <footer className="border-t bg-white py-2 sm:py-3 px-3 sm:px-6">
          <div className="container mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="mb-2 md:mb-0 text-center md:text-left">
                <p className="text-xs text-gray-600">
                  Réalisé avec <span className="text-red-500">❤</span> par <span className="text-[#203765]">Espérance AYIWAHOUN</span>.
                  <br className="hidden sm:block" />
                  <span className="sm:hidden"> </span>
                  &copy; {new Date().getFullYear()} Edge Attendance System. Tous droits réservés.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 sm:gap-4">
                <Link to="/confidentialite" className="text-xs text-[#1f3d7a] hover:text-blue-700">
                  Confidentialité
                </Link>
                <Link to="/conditions" className="text-xs text-[#1f3d7a] hover:text-blue-700">
                  Conditions
                </Link>
                <Link to="/aide" className="text-xs text-[#1f3d7a] hover:text-blue-700">
                  Aide
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </div>

      {/* Chatbot */}
      <Chatbot />
    </div>
  );
};

export default MainLayout;