import { z } from "zod";
import type { ModuleStatus, ModuleType } from "@/types";

export const moduleSchema = z.object({
  uid: z.number()
    .int("L'ID doit être un nombre entier")
    .positive("L'ID doit être un nombre positif"),
  name: z.string()
    .min(1, "Le nom du module est requis")
    .max(100, "Le nom ne peut pas dépasser 100 caractères"),
  description: z.string()
    .max(500, "La description ne peut pas dépasser 500 caractères")
    .optional(),
  emplacement: z.string()
    .max(200, "L'emplacement ne peut pas dépasser 200 caractères")
    .optional(),
  faceChecked: z.boolean(),
  rfidChecked: z.boolean(),
  status: z.enum(["online", "idle", "offline", "warning"] as const).optional(),
  created_by: z.string().optional(),
  updated_by: z.string().optional(),
  uptime: z.string().optional(),
  last_seen: z.string().optional(),
});

export type ModuleFormData = z.infer<typeof moduleSchema>;
