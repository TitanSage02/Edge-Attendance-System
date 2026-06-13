import React from "react";
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
import { Plus, Check, ChevronsUpDown, User, IdCard, BadgePlus, Layers, CreditCard } from "lucide-react";
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

// Form validation schema
const formSchema = z.object({
  student_id: z.string().min(1, "L'identifiant est requis"),
  first_name: z.string().min(1, "Le prénom est requis"),
  last_name: z.string().min(1, "Le nom est requis"),
  class_name: z.string().min(1, "La classe est requise"),
  rfid_card: z.string()
    .optional()
    .refine((val) => !val || /^[A-F0-9]{4,8}$/.test(val), {
      message: "L'UID RFID doit contenir entre 4 et 8 caractères hexadécimaux (0-9, A-F)"
    }),
});

type FormValues = z.infer<typeof formSchema>;

interface AddStudentFormProps {
  onAddStudent?: (studentData: FormValues) => void;
  classGroups?: string[];
  children?: React.ReactNode;
}

export function AddStudentForm({ onAddStudent, classGroups, children }: AddStudentFormProps) {
  const { success } = useUnifiedToast();
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
    mode: "onChange", // Validation en temps réel
  });

  // Handle form submission
  const onSubmit = (data: FormValues) => {
    setIsSubmitting(true);
    Promise.resolve(onAddStudent(data)).finally(() => {
      setIsSubmitting(false);
      success("Apprenant ajouté avec succès !");
    });
    setOpen(false);
    form.reset();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Ajouter un apprenant
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] p-0">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle className="text-xl font-bold">Ajouter un nouvel apprenant</DialogTitle>
          <DialogDescription className="text-gray-500 mt-1">
            Veuillez remplir les informations ci-dessous pour enregistrer un nouvel apprenant.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5 px-6 pb-6 pt-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="student_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">ID Étudiant</FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                        <IdCard className="h-4 w-4" />
                      </span>
                      <FormControl>
                        <Input className="pl-10" placeholder="STU2023001" {...field} />
                      </FormControl>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="class_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">Classe</FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
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
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">Nom</FormLabel>
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
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">Prénom</FormLabel>
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
            </div>
            <div className="mt-2">
              <FormField
                control={form.control}
                name="rfid_card"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-semibold">Carte RFID (optionnel)</FormLabel>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 z-10">
                        <CreditCard className="h-4 w-4" />
                      </span>
                      <FormControl>
                        <RfidUidInput 
                          className="pl-10" 
                          value={field.value}
                          onChange={field.onChange}
                          onBlur={field.onBlur}
                          name={field.name}
                        />
                      </FormControl>
                    </div>

                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter className="pt-4 flex flex-row justify-between gap-2">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" className="bg-[#1f3d7a] text-white hover:bg-[#16305c] flex items-center gap-2" disabled={isSubmitting || !form.formState.isValid}>
                {isSubmitting ? (
                  <svg className="animate-spin h-4 w-4 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                  </svg>
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                Ajouter
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}