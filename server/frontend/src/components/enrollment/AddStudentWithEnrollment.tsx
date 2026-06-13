import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RfidUidInput } from "@/components/ui/rfid-uid-input";
import { 
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { 
  Plus, 
  Check, 
  ChevronsUpDown, 
  User, 
  IdCard, 
  BadgePlus, 
  Layers, 
  CreditCard,
  Camera,
  UserPlus
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUnifiedToast } from "@/hooks/useUnifiedToast";
import { cn } from "@/lib/utils";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { StudentBase } from "@/types/studentTypes";

// Form validation schema pour l'ajout d'apprenant depuis l'enrôlement
const formSchema = z.object({
  student_id: z.string().min(1, "L'identifiant est requis"),
  first_name: z.string().min(1, "Le prénom est requis"),
  last_name: z.string().min(1, "Le nom est requis"),
  class_name: z.string().min(1, "La classe est requise"),
  rfid_card: z.string()
    .min(4, "L'UID RFID doit contenir au moins 4 caractères hexadécimaux")
    .max(8, "L'UID RFID ne peut pas dépasser 8 caractères hexadécimaux")
    .regex(/^[0-9A-Fa-f]+$/, "L'UID RFID ne peut contenir que des caractères hexadécimaux (0-9, A-F)")
    .refine((value) => value.length >= 4, {
      message: "L'UID RFID est requis pour l'enrôlement"
    }),
});

type FormValues = z.infer<typeof formSchema>;

interface AddStudentWithEnrollmentProps {
  onAddStudent: (studentData: StudentBase) => Promise<void>;
  classGroups?: string[];
  children?: React.ReactNode;
  promotion: string;
}

export function AddStudentWithEnrollment({ 
  onAddStudent, 
  classGroups, 
  children,
  promotion 
}: AddStudentWithEnrollmentProps) {
  const { success, error } = useUnifiedToast();
  const [open, setOpen] = React.useState(false);
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  
  // Initialize form
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      student_id: "",
      first_name: "",
      last_name: "",
      class_name: "",
      rfid_card: "",
    },
    mode: "onChange",
  });

  // Handle form submission
  const onSubmit = async (data: FormValues) => {
    setIsSubmitting(true);
    try {
      // Convertir les données du formulaire au format StudentBase
      const newStudentData: StudentBase = {
        id: data.student_id,
        firstName: data.first_name,
        lastName: data.last_name,
        classGroup: data.class_name,
        promotion: promotion,
        rfidUid: data.rfid_card,
        faceEnrolled: false,
        rfidEnrolled: true, // Puisqu'on a déjà le RFID
      };

      await onAddStudent(newStudentData);
      
      success("Apprenant créé avec succès ! Vous pouvez maintenant procéder à l'enrôlement facial.", {
        title: "Apprenant créé"
      });
      
      // Reset et fermer le dialog
      form.reset();
      setOpen(false);
    } catch (err) {
      error("Impossible de créer l'apprenant", { title: "Erreur de création" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button className="bg-green-600 hover:bg-green-700 text-white">
            <UserPlus className="h-4 w-4 mr-2" />
            Nouvel apprenant
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[650px] p-0">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle className="text-xl font-bold flex items-center">
            <Camera className="h-5 w-5 mr-2 text-green-600" />
            Ajouter un apprenant pour enrôlement
          </DialogTitle>
          <DialogDescription className="text-gray-500 mt-1">
            Créez un nouvel apprenant avec ses informations et carte RFID. Après validation, 
            vous pourrez immédiatement procéder à l'enrôlement facial.
          </DialogDescription>
        </DialogHeader>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5 px-6 pb-6 pt-2">
            {/* ID Étudiant et Carte RFID sur la même ligne */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="student_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold text-blue-700">
                      ID Étudiant *
                    </FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                        <IdCard className="h-4 w-4" />
                      </span>
                      <FormControl>
                        <Input 
                          className="pl-10 border-blue-200 focus:border-blue-500" 
                          placeholder="STU2025001" 
                          {...field} 
                        />
                      </FormControl>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="rfid_card"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold text-blue-600">
                      Carte RFID *
                    </FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10">
                        <CreditCard className="h-4 w-4" />
                      </span>
                      <FormControl>
                        <RfidUidInput 
                          className="pl-10 border-blue-200 focus:border-blue-500" 
                          placeholder="AB12CDEF"
                          value={field.value}
                          onChange={field.onChange}
                        />
                      </FormControl>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Prénom et Nom sur la même ligne */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">Prénom *</FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                        <User className="h-4 w-4" />
                      </span>
                      <FormControl>
                        <Input className="pl-10" placeholder="Kofi" {...field} />
                      </FormControl>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">Nom *</FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                        <BadgePlus className="h-4 w-4" />
                      </span>
                      <FormControl>
                        <Input className="pl-10" placeholder="Mensah" {...field} />
                      </FormControl>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Classe avec possibilité de création */}
            <FormField
              control={form.control}
              name="class_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-semibold">Classe *</FormLabel>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10">
                      <Layers className="h-4 w-4" />
                    </span>
                    <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            role="combobox"
                            aria-expanded={popoverOpen}
                            className={cn(
                              "w-full justify-between pl-9",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value
                              ? classGroups?.find(
                                  (cg) => cg.toLowerCase() === field.value.toLowerCase()
                                ) || field.value
                              : "Sélectionner ou créer une classe"}
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
                        <Command shouldFilter={false}>
                          <CommandInput
                            placeholder="Rechercher ou créer..."
                            onValueChange={(searchValue) => {
                              if (!classGroups?.some(cg => cg.toLowerCase() === searchValue.toLowerCase())) {
                                field.onChange(searchValue);
                              }
                            }}
                            value={field.value || ""}
                          />
                          <CommandList>
                            <CommandEmpty>
                              {field.value && !classGroups?.some(cg => cg.toLowerCase() === field.value.toLowerCase())
                                ? `Créer "${field.value}"`
                                : "Aucune classe trouvée."}
                            </CommandEmpty>
                            <CommandGroup>
                              {classGroups?.map((cg) => (
                                <CommandItem
                                  value={cg}
                                  key={cg}
                                  onSelect={(currentValue) => {
                                    form.setValue("class_name", currentValue === field.value ? "" : currentValue, { shouldValidate: true });
                                    setPopoverOpen(false);
                                  }}
                                >
                                  <Check
                                    className={cn(
                                      "mr-2 h-4 w-4",
                                      field.value && field.value.toLowerCase() === cg.toLowerCase()
                                        ? "opacity-100"
                                        : "opacity-0"
                                    )}
                                  />
                                  {cg}
                                </CommandItem>
                              ))}
                              {field.value && !classGroups?.some(cg => cg.toLowerCase() === field.value.toLowerCase()) && (
                                <CommandItem
                                  value={field.value}
                                  key={`create-${field.value}`}
                                  onSelect={() => {
                                    setPopoverOpen(false);
                                  }}
                                >
                                  <Plus className="mr-2 h-4 w-4" />
                                  Créer "{field.value}"
                                </CommandItem>
                              )}
                            </CommandGroup>
                          </CommandList>
                        </Command>
                      </PopoverContent>
                    </Popover>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Information sur la promotion */}
            {/* <div className="bg-blue-50 p-3 rounded-md border border-blue-200">
              <p className="text-sm text-blue-700">
                <strong>Promotion :</strong> {promotion}
              </p>
              <p className="text-xs text-blue-600 mt-1">
                La promotion est automatiquement attribuée selon les paramètres système.
              </p>
            </div> */}

            {/* Information sur le processus */}
            {/* <div className="bg-green-50 p-3 rounded-md border border-green-200">
              <h4 className="text-sm font-semibold text-green-700 mb-1">
                Après validation :
              </h4>
              <ul className="text-xs text-green-600 space-y-1">
                <li>• L'apprenant sera créé dans le système</li>
                <li>• Il sera automatiquement sélectionné pour l'enrôlement facial</li>
                <li>• Vous pourrez immédiatement prendre les 6 photos obligatoires</li>
              </ul>
            </div> */}

            {/* Boutons d'action */}
            <div className="flex justify-between pt-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setOpen(false)}
                disabled={isSubmitting}
              >
                Annuler
              </Button>
              
              <Button 
                type="submit" 
                className="bg-green-600 hover:bg-green-700 text-white flex items-center gap-2" 
                disabled={isSubmitting || !form.formState.isValid}
              >
                {isSubmitting ? (
                  <svg className="animate-spin h-4 w-4 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                  </svg>
                ) : (
                  <UserPlus className="h-4 w-4" />
                )}
                {isSubmitting ? "Création..." : "Créer et commencer l'enrôlement"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default AddStudentWithEnrollment;
