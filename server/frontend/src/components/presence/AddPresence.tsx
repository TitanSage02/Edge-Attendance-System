import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
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
import { Calendar } from "@/components/ui/calendar";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { CalendarIcon, Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { presenceApi } from "@/services/api/presence";
import { studentsApi } from "@/services/api/students";
import { modulesApi } from "@/services/api/modules";
import { Input } from "@/components/ui/input";
import { Module } from "@/types/moduleTypes";
import { StudentRead } from "@/types/studentTypes";

// Form validation schema
const formSchema = z.object({
  student_id: z.string().min(1, "L'étudiant est requis"),
  status: z.boolean().default(true),
  timestamp: z.string().min(1, "L'heure est requise"),
});

type FormValues = z.infer<typeof formSchema>;

interface AddPresenceDialogProps {
  onAddPresence?: (presenceData: FormValues) => void;
  children?: React.ReactNode;
}

export function AddPresenceDialog({ onAddPresence, children }: AddPresenceDialogProps) {
  const { error, success } = useUnifiedToast();
  const [open, setOpen] = React.useState(false);
  const [students, setStudents] = useState<StudentRead[]>([]);
  const [filteredStudents, setFilteredStudents] = useState<StudentRead[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [loading, setLoading] = useState(false);const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      student_id: "",
      status: true,
      timestamp: (() => {
        const now = new Date();
        now.setHours(now.getHours() + 1); // GMT+1
        return now.toISOString().slice(0, 16);
      })(),
    },
  });
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Charger uniquement les étudiants
        const studentsData = await studentsApi.getStudents();
        setStudents(studentsData);
        setFilteredStudents(studentsData);
      } catch (loadError) {
        console.error("Erreur lors du chargement des données:", loadError);
        error("Impossible de charger les données des étudiants", { title: "Erreur" });
      } finally {
        setLoading(false);
      }
    };

    if (open) {
      // Réinitialiser la date et l'heure à maintenant GMT+1 à chaque ouverture
      const now = new Date();
      now.setHours(now.getHours() + 1); // GMT+1
      form.setValue("timestamp", now.toISOString().slice(0, 16));
      
      fetchData();
      // Réinitialiser le filtre de classe
      setSelectedClass("");
    }
  }, [open, form]);

  // Effet pour filtrer les étudiants par classe
  useEffect(() => {
    if (selectedClass === "") {
      setFilteredStudents(students);
    } else {
      setFilteredStudents(students.filter(student => student.classGroup === selectedClass));
    }
    // Réinitialiser la sélection d'étudiant quand on change de classe
    form.setValue("student_id", "");
  }, [selectedClass, students, form]);

  // Obtenir la liste unique des classes
  const uniqueClasses = Array.from(new Set(students.map(student => student.classGroup)))
    .filter(Boolean)
    .sort();

  // Handle form submission
  const onSubmit = async (data: FormValues) => {
    try {
      await presenceApi.addAttendance({
        student_id: data.student_id,
        module_uid: 0, // Module manuel
        status: data.status,
        timestamp: data.timestamp,      });
        success("Présence enregistrée avec succès", { title: "Succès" });
      
      // Réinitialiser le formulaire avec une nouvelle timestamp GMT+1
      const resetTime = new Date();
      resetTime.setHours(resetTime.getHours() + 1); // GMT+1
      form.reset({
        student_id: "",
        status: true,
        timestamp: resetTime.toISOString().slice(0, 16),
      });
      setOpen(false);

      if (onAddPresence) {
        onAddPresence(data);
      }    
    } catch (submitError: any) {
      console.error("Erreur lors de l'enregistrement de la présence:", submitError);
      
      // Gestion spécifique des erreurs
      if (submitError.response?.status === 400) {
        error(submitError.response.data.detail || "Données invalides", { title: "Erreur de validation" });
      } else if (submitError.response?.status === 409) {
        error("L'étudiant a déjà une présence enregistrée pour aujourd'hui", { title: "Conflit" });
      } else {
        error("Une erreur est survenue lors de l'enregistrement de la présence", { title: "Erreur" });
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {/* {children || (
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Présence manuelle
          </Button>
        )} */}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Enregistrer une présence manuellement</DialogTitle>
          <DialogDescription>
            Ajoutez manuellement une présence pour un étudiant.
          </DialogDescription>
        </DialogHeader>        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-2">
            {/* Filtre par classe */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Filtrer par classe
              </label>
              <Select
                value={selectedClass}
                onValueChange={setSelectedClass}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Toutes les classes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Toutes les classes</SelectItem>
                  {uniqueClasses.map((classe) => (
                    <SelectItem key={classe} value={classe}>
                      {classe}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <FormField
              control={form.control}
              name="student_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Étudiant</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                    disabled={loading}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Sélectionner un étudiant" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {filteredStudents.map((student) => (
                        <SelectItem key={student.id} value={student.id || ""}>
                          {student.firstName} {student.lastName}
                          {selectedClass === "" && (
                            <span className="text-gray-500 ml-2">({student.classGroup})</span>
                          )}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="timestamp"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Heure</FormLabel>
                  <FormControl>
                    <Input
                      type="datetime-local"
                      {...field}
                      disabled={loading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel>Type de présence</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={(value) => field.onChange(value === "true")}
                      defaultValue={field.value ? "true" : "false"}
                      className="flex flex-col space-y-1"
                    >
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="true" />
                        </FormControl>
                        <FormLabel className="font-normal">
                          Entrée
                        </FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl>
                          <RadioGroupItem value="false" />
                        </FormControl>
                        <FormLabel className="font-normal">
                          Sortie
                        </FormLabel>
                      </FormItem>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="submit" disabled={loading}>
                {loading ? "Enregistrement..." : "Enregistrer"}
              </Button>
            </DialogFooter>
          
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}