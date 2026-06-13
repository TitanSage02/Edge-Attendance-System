import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import {
  Home,
  Users,
  Calendar,
  Server,
  Bell,
  Settings,
  FileText,
  Shield,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  isMobile?: boolean;
}

const Sidebar = ({ isOpen, onToggle, isMobile = false }: SidebarProps) => {
  const { pathname } = useLocation();
  const { hasRole } = useAuth();

  const sidebarLinks = [
    {
      title: "Tableau de bord",
      href: "/dashboard",
      icon: Home,
      roles: ["admin", "pedagogical", "technician"],
    },
    {
      title: "Apprenants",
      href: "/apprenants",
      icon: Users,
      roles: ["admin", "pedagogical"],
    },
    {
      title: "Présences",
      href: "/presences",
      icon: Calendar,
      roles: ["admin", "pedagogical"],
    },
    {
      title: "Modules",
      href: "/modules",
      icon: Server,
      roles: ["admin", "technician"],
    },
    {
      title: "Alertes",
      href: "/alertes",
      icon: Bell,
      roles: ["admin", "technician"],
    },
    {
      title: "Paramètres",
      href: "/parametres",
      icon: Settings,
      roles: ["admin"],
    },
    {
      title: "Gestion Utilisateurs",
      href: "/admin-utilisateurs",
      icon: Shield,
      roles: ["admin"],
    },
  ];
  return (
    <aside
      className={cn(
        "h-screen bg-white border-r border-gray-200 transition-all duration-300 ease-in-out overflow-hidden",
        isMobile && !isOpen && "hidden",
        isMobile && isOpen ? "w-64" : isMobile ? "w-0" : isOpen ? "w-64" : "w-20"
      )}
    >
      <div className="h-full flex flex-col">        
        {/* Logo/header */}
        <div className="h-16 flex items-center justify-between px-4 border-b">
          {isOpen ? (
            <div className="text-2xl font-bold text-[#1f3d7a]">
              <img src={import.meta.env.VITE_LOGO_PATH || '/logo.png'} alt="Logo Edge Attendance System" className="h-8" />
            </div>
          ) : (
            <div className="w-full text-center text-2xl font-bold text-[#1f3d7a]">C</div>
          )}
          {(isMobile || isOpen) && (
            <Button
              variant="ghost"
              size="icon"
              className="ml-auto"
              onClick={onToggle}
              aria-label={isOpen ? "Réduire la barre latérale" : "Agrandir la barre latérale"}
            >
              {isOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          )}
        </div>

        {/* Navigation links */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {sidebarLinks.map((link) => {
            if (!hasRole(link.roles as any)) return null;
            const isActive = pathname === link.href;

            return (
              <Link
                key={link.href}
                to={link.href}
                className={cn(
                  "flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-colors",
                  isActive
                    ? "bg-[#1f3d7a] text-white"
                    : "text-gray-700 hover:bg-gray-100"
                )}
                title={!isOpen ? link.title : undefined}
              >
                <link.icon className={cn("h-5 w-5", isOpen ? "mr-3" : "mx-auto")} />
                {isOpen && <span>{link.title}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t text-center text-xs text-gray-500">
          {isOpen ? "Edge Attendance System v1.0" : "v1.0"}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;