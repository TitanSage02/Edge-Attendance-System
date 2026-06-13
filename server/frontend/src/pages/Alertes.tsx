import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import {
  AlertTriangle,
  Search,
  Calendar,
  CheckCircle2,
  Archive
} from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/types/alertTypes";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { Link } from "react-router-dom";
import { useAlertsRealtime } from "@/services/websocket/useAlertsRealtime";

const Alertes = () => {
  const { alerts, loading, error, resolveAlert } = useAlertsRealtime();
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterAcknowledged, setFilterAcknowledged] = useState<string>("all");
  const { success } = useUnifiedToast();
  
  const filteredAlerts = alerts.filter((alert) => {
    // Filtrage par recherche
    const matchesSearch = 
      searchTerm === "" || 
      alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (alert.moduleName && alert.moduleName.toLowerCase().includes(searchTerm.toLowerCase()));
    
    // Filtrage par type
    const matchesType = 
      filterType === "all" || 
      alert.type === filterType;
    
    // Filtrage par sévérité
    const matchesSeverity = 
      filterSeverity === "all" || 
      alert.severity === filterSeverity;
      
    // Filtrage par statut d'acquittement
    const matchesAcknowledged = 
      filterAcknowledged === "all" ||
      (filterAcknowledged === "acknowledged" && alert.resolved) || 
      (filterAcknowledged === "unacknowledged" && !alert.resolved);
    
    return matchesSearch && matchesType && matchesSeverity && matchesAcknowledged;
  });
    const handleAcknowledge = (id: string) => {
    resolveAlert(id);
    success("L'alerte a été marquée comme acquittée avec succès.", { title: "Alerte acquittée" });
  };
  
  const handleArchive = (id: string) => {
    // TODO: Implémenter l'archivage via l'API
    success("L'alerte a été archivée avec succès.", { title: "Alerte archivée" });
  };
  
  const getSeverityColor = (severity: string) => {
    switch(severity) {
      case "critical": return "bg-red-100 text-red-800 border-red-200";
      case "warning": return "bg-amber-100 text-amber-800 border-amber-200";
      case "info": return "bg-blue-100 text-blue-800 border-blue-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };
  
  const getTypeLabel = (type: string) => {
    switch(type) {
      case "module_offline": return "Module hors ligne";
      case "temperature": return "Température";
      case "auth_failure": return "Authentification";
      case "system": return "Système";
      default: return type;
    }
  };
  
  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">Chargement des alertes...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center max-w-md mx-auto p-8">
            <div className="text-green-500 text-6xl mb-6">✓</div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Tout va bien !</h2>
            <p className="text-gray-600 text-lg leading-relaxed">{error}</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (alerts.length === 0) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-green-500 text-4xl mb-4">✓</div>
            <p className="text-gray-600">Aucune alerte en cours</p>
          </div>
        </div>
      </MainLayout>
    );
  }
  
  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight text-[#1f3d7a]">Alertes</h1>
          
          <div className="flex gap-2">
            <Link to="/alertes/archives">
              <Button variant="outline" className="bg-white hover:bg-gray-50">
                <Archive className="h-4 w-4 mr-2" />
                Archives ({alerts.filter(a => a.resolved).length})
              </Button>
            </Link>
          </div>
        </div>
        
        {/* Filtres */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              placeholder="Rechercher..."
              className="pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger>
              <SelectValue placeholder="Type d'alerte" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              <SelectItem value="module_offline">Module hors ligne</SelectItem>
              <SelectItem value="temperature">Température</SelectItem>
              <SelectItem value="auth_failure">Authentification</SelectItem>
              <SelectItem value="system">Système</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={filterSeverity} onValueChange={setFilterSeverity}>
            <SelectTrigger>
              <SelectValue placeholder="Sévérité" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Toutes les sévérités</SelectItem>
              <SelectItem value="critical">Critique</SelectItem>
              <SelectItem value="warning">Avertissement</SelectItem>
              <SelectItem value="info">Information</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={filterAcknowledged} onValueChange={setFilterAcknowledged}>
            <SelectTrigger>
              <SelectValue placeholder="Statut" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              <SelectItem value="acknowledged">Acquittées</SelectItem>
              <SelectItem value="unacknowledged">Non acquittées</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        {/* Liste des alertes */}
        {filteredAlerts.length > 0 ? (
          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <Card key={alert.id} className={`bg-white hover:shadow-sm transition-all ${alert.resolved ? '' : 'border-l-4 border-l-red-500'}`}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className={`h-4 w-4 ${alert.resolved ? 'text-gray-500' : 'text-red-500'}`} />
                      <CardTitle className="text-base">{alert.message}</CardTitle>
                    </div>
                    <Badge className={`${getSeverityColor(alert.severity)} border`}>
                      {alert.severity === "critical" ? "Critique" : 
                       alert.severity === "warning" ? "Avertissement" : "Information"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500 mb-1">Type</p>
                      <p>{getTypeLabel(alert.type)}</p>
                    </div>
                    
                    {alert.moduleName && (
                      <div>
                        <p className="text-gray-500 mb-1">Module</p>
                        <p>{alert.moduleName}</p>
                      </div>
                    )}
                    
                    <div>
                      <p className="text-gray-500 mb-1">Détectée le</p>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5 text-gray-500" />
                        <p>{format(new Date(alert.timestamp), "dd/MM/yyyy HH:mm", { locale: fr })}</p>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2">
                      {!alert.resolved && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleAcknowledge(alert.id)}
                        >
                          <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                          Acquitter
                        </Button>
                      )}
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleArchive(alert.id)}
                      >
                        <Archive className="h-3.5 w-3.5 mr-1" />
                        Archiver
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="rounded-full bg-gray-100 p-3 mb-4">
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              </div>
              <h3 className="text-lg font-medium mb-2">Aucune alerte active</h3>
              <p className="text-gray-500 text-center max-w-md">
                Il n'y a actuellement aucune alerte active correspondant à vos critères de filtrage.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export default Alertes;
