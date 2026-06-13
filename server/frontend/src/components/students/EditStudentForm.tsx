import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RfidUidInput } from "@/components/ui/rfid-uid-input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { StudentBase } from "@/types/studentTypes";


// Formulaire pour modifier un étudiant
export const EditStudentForm = ({ 
  student, 
  onSubmit,
  classGroups,
}: { 
  student: StudentBase, 
  onSubmit: (data: Partial<StudentBase>) => void,
  classGroups: string[],
}) => {
  const [firstName, setFirstName] = useState(student.firstName);
  const [lastName, setLastName] = useState(student.lastName);
  const [rfidUid, setRfidUid] = useState(student.rfidUid || "");
  const [classGroup, setClassGroup] = useState(student.classGroup);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      firstName,
      lastName,
      classGroup,
      rfidUid: rfidUid || undefined, // Envoie undefined si vide
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="editFirstName">Prénom</Label>
          <Input
            id="editFirstName"
            required
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="editLastName">Nom</Label>
          <Input
            id="editLastName"
            required
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="editRfidUid">Carte RFID</Label>
        <RfidUidInput
          id="editRfidUid"
          value={rfidUid}
          onChange={setRfidUid}
        />
        <p className="text-xs text-muted-foreground">
          Format: 8 caractères hexadécimaux (ex: AB:12:CD:EF)
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="editClass">Classe</Label>
        <Select value={classGroup} onValueChange={setClassGroup}>
          <SelectTrigger id="editClass">
            <SelectValue placeholder="Sélectionner une classe" />
          </SelectTrigger>
          <SelectContent>
            {classGroups.map((group) => (
              <SelectItem key={group} value={group}>{group}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      <div className="pt-2 text-sm text-gray-500">
        Promotion: {student.promotion}
      </div>
      
      {/* <div className="pt-2 text-sm text-gray-500">
        <div className="flex flex-col space-y-1">
          <div>
            <span className="font-medium">Statut d'inscription:</span> {student.enrolled ? "Inscrit" : "Non inscrit"} 
            <span className="text-xs ml-1">(modifiable via système)</span>
          </div>
          <div>
            <span className="font-medium">Visage enrôlé:</span> {student.faceEnrolled ? "Oui" : "Non"} 
            <span className="text-xs ml-1">(modifiable via système)</span>
          </div>
        </div>
      </div> */}
      
      <DialogFooter>
        <DialogTrigger asChild>
          <Button type="button" variant="outline">Annuler</Button>
        </DialogTrigger>
        <Button type="submit">Enregistrer</Button>
      </DialogFooter>
    </form>
  );
};
