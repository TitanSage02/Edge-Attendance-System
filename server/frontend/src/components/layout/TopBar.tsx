import { useState, useEffect } from "react";
import { Bell, Menu, User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { useIsMobile } from "@/hooks/use-mobile";
import { Link } from "react-router-dom";
import { websocketService } from "@/services/websocket";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";

import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface TopBarProps {
  onToggleSidebar: () => void;
  pageTitle: string;
}

const TopBar = ({ onToggleSidebar, pageTitle }: TopBarProps) => {
  const { user, logout } = useAuth();
  const isMobile = useIsMobile();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // S'abonner aux notifications
    const unsubscribe = websocketService.subscribe("alerts", (data) => {
      const newNotification: Notification = {
        id: data.id,
        type: data.type,
        title: data.title,
        message: data.message,
        timestamp: data.timestamp,
        read: false
      };

      setNotifications(prev => {
        const updated = [newNotification, ...prev].slice(0, 50); // Garder les 50 dernières notifications
        setUnreadCount(updated.filter(n => !n.read).length);
        return updated;
      });
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const markAsRead = (notificationId: string) => {
    setNotifications(prev => {
      const updated = prev.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      );
      setUnreadCount(updated.filter(n => !n.read).length);
      return updated;
    });
  };

  const markAllAsRead = () => {
    setNotifications(prev => {
      const updated = prev.map(n => ({ ...n, read: true }));
      setUnreadCount(0);
      return updated;
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "error":
        return "🔴";
      case "warning":
        return "🟠";
      case "success":
        return "🟢";
      default:
        return "🔵";
    }
  };

  return (
    <header className="bg-white/95 backdrop-blur-sm shadow-sm z-10 sticky top-0 border-b border-gray-100 w-full">
      <div className="h-[4rem] min-h-[4rem] flex items-center justify-between px-2 sm:px-4"> 
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onToggleSidebar}
            className="mr-1 sm:mr-2"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <h1 className="text-base sm:text-lg font-semibold text-[#1f3d7a] truncate max-w-[150px] xs:max-w-[200px] sm:max-w-xs md:max-w-sm lg:max-w-md">
            {pageTitle}
          </h1>
        </div>

        <div className="flex items-center space-x-1 sm:space-x-2">
          {/* Notifications dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                )}
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end" className="w-[280px] sm:w-80 bg-white">
              <div className="flex items-center justify-between px-2 py-1.5">
                <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                {unreadCount > 0 && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={markAllAsRead}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    Tout marquer comme lu
                  </Button>
                )}
              </div>
              <DropdownMenuSeparator />
              <div className="max-h-[300px] overflow-auto">
                {notifications.length === 0 ? (
                  <div className="px-2 py-3 text-center text-sm text-gray-500">
                    Aucune notification
                  </div>
                ) : (
                  notifications.map((notification) => (
                    <DropdownMenuItem
                      key={notification.id}
                      className={`cursor-pointer p-3 ${!notification.read ? 'bg-blue-50' : ''}`}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div>
                        <div className="flex items-start gap-2">
                          <span className="text-lg">{getNotificationIcon(notification.type)}</span>
                          <div>
                            <p className="font-medium">{notification.title}</p>
                            <p className="text-sm text-gray-500">{notification.message}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              {(() => {
                                const dateObj = new Date(notification.timestamp);
                                if (dateObj instanceof Date && !isNaN(dateObj.getTime())) {
                                  return formatDistanceToNow(dateObj, {
                                    addSuffix: true,
                                    locale: fr
                                  });
                                }
                                return "Date inconnue";
                              })()}
                            </p>
                          </div>
                        </div>
                      </div>
                    </DropdownMenuItem>
                  ))
                )}
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer justify-center font-medium">
                Voir toutes les notifications
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User profile dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-1 sm:gap-2 px-2 sm:px-3">
                <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#1f3d7a] flex items-center justify-center text-white text-xs sm:text-sm">
                  {user?.firstName?.charAt(0) || "U"}
                </div>
                {!isMobile && user?.firstName && (
                  <span className="hidden md:block font-medium text-sm truncate max-w-[100px]">
                    {user?.firstName} {user?.lastName}
                  </span>
                )}
                {(isMobile || !user?.firstName) && user?.lastName && (
                  <span className="font-medium text-sm truncate max-w-[100px] md:hidden">
                    {user?.lastName}
                  </span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-white">
              <DropdownMenuLabel>Mon compte</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer">
                <Link to="/profile" className="flex items-center w-full">
                  <User className="mr-2 h-4 w-4" />
                  <span>Profil</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Déconnexion</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
};

export default TopBar;