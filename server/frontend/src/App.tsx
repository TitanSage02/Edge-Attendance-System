
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/ui/ErrorBoundary";

// Pages
import Index from "./pages/Index";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Logout from "./pages/Logout";
import NotFound from "./pages/NotFound";
import Apprenants from "./pages/Apprenants";
import Presences from "./pages/Presences";
import Modules from "./pages/Modules";
import Alertes from "./pages/Alertes";
import AlertesArchives from "./pages/AlertesArchives";
import Parametres from "./pages/Parametres";
import AdminUtilisateurs from "./pages/AdminUtilisateurs";
import Profile from "./pages/Profile";
import Confidentialite from "./pages/Confidentialite";
import Conditions from "./pages/Conditions";
import Aide from "./pages/Aide";
import FaceEnrollment from "./pages/FaceEnrollment";

const queryClient = new QueryClient();

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<Index />} />            
                <Route path="/login" element={<Login />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/apprenants" element={<Apprenants />} />
                <Route path="/enrollment" element={<FaceEnrollment />} />
                <Route path="/presences" element={<Presences />} />
                <Route path="/modules" element={<Modules />} />
                <Route path="/alertes" element={<Alertes />} />
                <Route path="/alertes/archives" element={<AlertesArchives />} />
                <Route path="/parametres" element={<Parametres />} />
                <Route path="/admin-utilisateurs" element={<AdminUtilisateurs />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/confidentialite" element={<Confidentialite />} />
                <Route path="/conditions" element={<Conditions />} />
                <Route path="/aide" element={<Aide />} />
                <Route path="/logout" element={<Logout />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
          </TooltipProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
