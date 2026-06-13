// Fonction utilitaire pour vérifier la validité d'une date
const isValidDate = (d: any) => d instanceof Date && !isNaN(d.getTime());
import React, { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import MainLayout from "../components/layout/MainLayout";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import {
  CalendarIcon,
  Search,
  Download,
  UserCheck,
  Plus,
  Info,
  MoreHorizontal,
  Clock,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

import { AddPresenceDialog } from "@/components/presence/AddPresence";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { presenceApi } from "@/services/api/presence";
import { Attendance } from "@/services/api/presence";
import { AttendanceSummary } from "@/types";

// Interface pour une activité (entrée ou sortie)
interface Activity {
  time: string;
  type: 'entry' | 'exit';
}

// Interface pour les données groupées par étudiant
interface GroupedStudentAttendance {
  student_id: string;
  student_name: string;
  status: boolean;
  activities: Activity[];
  sessionCount: number;
}

// Interface pour les statistiques calculées
interface CalculatedStats {
  total_students: number;
  present_count: number;
  absent_count: number;
  presence_percentage: number;
}

const Presences: React.FC = () => {
  const { error: showError } = useUnifiedToast();
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presences, setPresences] = useState<Attendance[]>([]);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [classes, setClasses] = useState<{ id: string; name: string }[]>([]);

  // Charger les classes
  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const data = await presenceApi.getClasses();
        setClasses(data);
        if (data.length > 0) {
          setSelectedClass(data[0].id);
        }      
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Impossible de charger la liste des classes";
        setError(errorMessage);
        showError(errorMessage, { title: "Erreur" });
      }
    };    
    fetchClasses();
  }, [showError]);

  // Charger les présences et le résumé
  useEffect(() => {
    const fetchData = async () => {
      if (!selectedClass) return;

      try {
        setLoading(true);
        setError(null);
        
        const [presencesResponse, summaryResponse] = await Promise.all([
          presenceApi.getAttendance({
            date_from: format(selectedDate, 'yyyy-MM-dd'),
            date_to: format(selectedDate, 'yyyy-MM-dd'),
            class_group: selectedClass
          }),
          presenceApi.getDailySummary({
            target_date: format(selectedDate, 'yyyy-MM-dd'),
            class_group: selectedClass
          })
        ]);
        
        // console.log('Réponse des présences:', presencesResponse);
        // console.log('Réponse du résumé:', summaryResponse);

        if (Array.isArray(presencesResponse)) {
          setPresences(presencesResponse);
        } else {
          setPresences([]);
        }
        
        if (summaryResponse) {
          setSummary(summaryResponse);
        }     
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Erreur lors du chargement des données";
        setError(errorMessage);
        
        showError(errorMessage, { title: "Erreur" });
      } finally {
        setLoading(false);
      }
    };    
    fetchData();
  }, [selectedDate, selectedClass, showError]);

  // Regrouper les présences par étudiant
  const groupedPresences = useMemo(() => {
    const grouped = new Map<string, GroupedStudentAttendance>();

    presences.forEach((presence) => {
      const id = presence.student_id;
      const name = presence.student
        ? `${presence.student.firstName} ${presence.student.lastName}`
        : "Non renseigné";

      if (!grouped.has(id)) {
        grouped.set(id, {
          student_id: id,
          student_name: name,
          status: false,
          activities: [],
          sessionCount: 0
        });
      }

      const entry = presence.entry_time && { time: presence.entry_time, type: 'entry' as const };
      const exit = presence.exit_time && { time: presence.exit_time, type: 'exit' as const };

      if (entry) grouped.get(id)!.activities.push(entry);
      if (exit) grouped.get(id)!.activities.push(exit);
    });

    // Forcer l'alternance stricte entrée/sortie, en commençant par une entrée
    grouped.forEach((student) => {
      // Tri chronologique
      student.activities.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
      // Forçage alternance stricte
      const alternated: Activity[] = [];
      let expected: 'entry' | 'exit' = 'entry';
      for (const act of student.activities) {
        // On commence toujours par une entrée
        alternated.push({ ...act, type: expected });
        expected = expected === 'entry' ? 'exit' : 'entry';
      }
      student.activities = alternated;
    });

    return Array.from(grouped.values());
  }, [presences]);

  // Calculer les statistiques selon les nouvelles règles
  const calculatedStats = useMemo((): CalculatedStats => {
    if (!summary) {
      return {
        total_students: 0,
        present_count: 0,
        absent_count: 0,
        presence_percentage: 0
      };
    }

    // Un étudiant est présent s'il a au moins une activité (entrée)
    const present_students = groupedPresences.filter(
      (s) => s.activities.length > 0
    ).length;

    const absent_count = Math.max(0, summary.total_students - present_students);

    return {
      total_students: summary.total_students,
      present_count: present_students,
      absent_count,
      presence_percentage: summary.total_students > 0
        ? (present_students / summary.total_students) * 100
        : 0
    };
  }, [groupedPresences, summary]);

  // Filtrer les présences groupées en fonction de la recherche
  const filteredPresences = groupedPresences?.filter(
    (presence) =>
      presence.student_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      presence.student_name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Trier les présences filtrées par ordre chronologique (première activité)
  const sortedFilteredPresences = useMemo(() => {
    return filteredPresences.sort((a, b) => {
      const aFirstActivity = a.activities.length > 0 ? a.activities[0].time : "";
      const bFirstActivity = b.activities.length > 0 ? b.activities[0].time : "";
      
      if (!aFirstActivity && !bFirstActivity) return 0;
      if (!aFirstActivity) return 1;
      if (!bFirstActivity) return -1;
      
      return new Date(aFirstActivity).getTime() - new Date(bFirstActivity).getTime();
    });
  }, [filteredPresences]);

  const handleExport = async () => {
    try {
      const blob = await presenceApi.exportPresences({
        target_date: format(selectedDate, 'yyyy-MM-dd'),
        class_group: selectedClass
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `presences_${format(selectedDate, 'yyyy-MM-dd')}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);    
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erreur lors de l'exportation";
      showError(errorMessage, { title: "Erreur" });
    }
  };

  return (
    <MainLayout> 
      <div className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        
        {/* Page header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-display font-bold tracking-tight">Registre des présences</h1>
            <p className="text-muted-foreground">
              Consultez et gérez les présences des étudiants
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" className="hidden md:flex" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Exporter
            </Button>
            <AddPresenceDialog />
          </div>
        </div>

        {/* Filters bar */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="grid sm:grid-cols-3 gap-4 flex-1">
            {/* Date selector */}
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "justify-start text-left font-normal w-full",
                    !selectedDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {selectedDate ? (
                    format(selectedDate, "PPP", { locale: fr })
                  ) : (
                    <span>Choisir une date</span>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  initialFocus
                  className={cn("p-3 pointer-events-auto")}
                />
              </PopoverContent>
            </Popover>

            {/* Class selector */}
            <Select value={selectedClass} onValueChange={setSelectedClass}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner une classe" />
              </SelectTrigger>
              <SelectContent>
                {classes.map((classItem) => (
                  <SelectItem key={classItem.id} value={classItem.id}>
                    {classItem.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher un étudiant..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Statistics summary */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="md:col-span-4 bg-white">
            <CardContent className="p-6 ">
              <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Élèves inscrits</p>
                  <p className="text-2xl font-semibold">{calculatedStats.total_students}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Présents</p>
                  <p className="text-2xl font-semibold text-green-600">{calculatedStats.present_count}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Absents</p>
                  <p className="text-2xl font-semibold text-red-600">{calculatedStats.absent_count}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Taux de présence</p>
                  <p className="text-2xl font-semibold text-primary">
                    {calculatedStats.presence_percentage.toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Presence table */}
        <Card className="bg-white">
          <CardHeader className="pb-0">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <CardTitle className="text-lg">
                Présences pour {classes.find((c) => c.id === selectedClass)?.name || "..."} - {selectedDate ? format(selectedDate, "d MMMM yyyy", { locale: fr }) : ""}
              </CardTitle>
              <div className="flex items-center text-sm text-muted-foreground space-x-2">
                <div className="flex items-center">
                  <div className="bg-green-100 rounded-full p-1 mr-1">
                    <CheckCircle2 className="w-3 h-3 text-green-600" />
                  </div>
                  <span>Présent</span>
                </div>
                <div className="flex items-center">
                  <div className="bg-red-100 rounded-full p-1 mr-1">
                    <XCircle className="w-3 h-3 text-red-600" />
                  </div>
                  <span>Absent</span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10"></TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead className="w-[250px]">Étudiant</TableHead>
                    <TableHead className="text-center">Activités</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={4} className="h-24 text-center">
                        <div className="flex flex-col items-center justify-center gap-2">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                          <span>Chargement en cours...</span>
                        </div>
                      </TableCell>
                    </TableRow>                  
                    ) : sortedFilteredPresences.length > 0 ? (
                    sortedFilteredPresences.map((presence) => (
                      <TableRow key={presence.student_id}>
                        <TableCell>
                          <div
                            className={cn(
                              "w-3 h-3 rounded-full",
                              presence.status ? "bg-green-500" : "bg-red-500"
                            )}
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {presence.student_id || "Non renseigné"}
                        </TableCell>
                        <TableCell>
                          {presence.student_name}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex flex-wrap gap-1 justify-center">
                            {presence.activities.length > 0 ? (
                              presence.activities.map((activity, index) => {
                                const dateObj = new Date(activity.time);
                                const displayTime = isValidDate(dateObj)
                                  ? format(new Date(dateObj.getTime() - 60 * 60 * 1000), 'HH:mm')
                                  : null;
                                return (
                                  <span
                                    key={index}
                                    className={cn(
                                      "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
                                      activity.type === 'entry'
                                        ? "bg-green-100 text-green-800"
                                        : "bg-red-100 text-red-800"
                                    )}
                                  >
                                    {activity.type === 'entry' ? (
                                      <>
                                        <CheckCircle2 className="w-3 h-3" />
                                        <span>
                                          Entrée {displayTime ?? <span className="text-muted-foreground">Heure invalide</span>}
                                        </span>
                                      </>
                                    ) : (
                                      <>
                                        <XCircle className="w-3 h-3" />
                                        <span>
                                          Sortie {displayTime ?? <span className="text-muted-foreground">Heure invalide</span>}
                                        </span>
                                      </>
                                    )}
                                  </span>
                                );
                              })
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} className="h-24 text-center">
                        <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                          <Info className="h-8 w-8" />
                          <span>Aucune présence enregistrée pour cette date</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default Presences;