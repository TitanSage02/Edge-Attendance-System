import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Module } from "@/types/moduleTypes";
import { DialogFooter } from "@/components/ui/dialog";
import { moduleSchema, type ModuleFormData } from "@/schemas/moduleSchemas";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

interface ModuleFormProps {
  module?: Module;
  onSubmit: (data: Partial<Module>) => void;
  onCancel: () => void;
}

const ModuleForm = ({ module, onSubmit, onCancel }: ModuleFormProps) => {
  const form = useForm<ModuleFormData>({
    resolver: zodResolver(moduleSchema),
    defaultValues: {
      uid: module?.uid || 0, 
      name: module?.name || "",
      description: module?.description || "",
      emplacement: module?.emplacement || "",
      faceChecked: module?.faceChecked || false,
      rfidChecked: module?.rfidChecked || false,
    },
  });

  const handleSubmit = (data: ModuleFormData) => {
    if (!data.faceChecked && !data.rfidChecked) {
      form.setError("faceChecked", {
        type: "custom",
        message: "Au moins une méthode d'authentification doit être sélectionnée",
      });
      form.setError("rfidChecked", {
        type: "custom",
        message: "Au moins une méthode d'authentification doit être sélectionnée",
      });
      return;
    }

    const moduleData: Partial<Module> = {
      ...data,
      status: module ? undefined : "offline", // Statut par défaut pour les nouveaux modules
    };

    onSubmit(moduleData);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="uid"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>ID du module</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="04627"
                      {...field}
                      value={field.value || ""}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                      disabled={!!module} // Désactivé en mode édition
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nom du module</FormLabel>
                  <FormControl>
                    <Input placeholder="E1, S1, etc." {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Input placeholder="Description courte du module" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
{/* 
          <FormField
            control={form.control}
            name="emplacement"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Emplacement</FormLabel>
                <FormControl>
                  <Input placeholder="S101, Amphithéâtre, etc." {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          /> */}

          <div className="space-y-2">
            <Label className="block mb-2">Méthodes d'authentification</Label>
            <div className="flex flex-col space-y-2">
              <FormField
                control={form.control}
                name="rfidChecked"
                render={({ field }) => (
                  <FormItem className="flex items-center space-x-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <FormLabel className="!mt-0">RFID</FormLabel>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="faceChecked"
                render={({ field }) => (
                  <FormItem className="flex items-center space-x-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <FormLabel className="!mt-0">Reconnaissance faciale</FormLabel>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Annuler
          </Button>
          <Button type="submit">
            {module ? "Mettre à jour" : "Ajouter"}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
};

export default ModuleForm;
