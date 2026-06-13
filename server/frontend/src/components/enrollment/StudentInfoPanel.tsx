import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { RfidUidInput } from "@/components/ui/rfid-uid-input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { User, CreditCard, Save, RotateCcw, Check, ChevronsUpDown, Plus } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { cn } from "@/lib/utils";

interface StudentInfo {
  id: string;
  firstName: string;
  lastName: string;
  rfidUid: string | null;
  classGroup: string;
  faceEnrolled: boolean;
}

interface StudentInfoPanelProps {
  student: StudentInfo;
  onUpdateStudent: (data: Partial<StudentInfo>) => Promise<void>;
  isLoading?: boolean;
  classGroups?: string[];
}

const StudentInfoPanel: React.FC<StudentInfoPanelProps> = ({
  student,
  onUpdateStudent,
  isLoading = false,
  classGroups = []
}) => {
  const [editableInfo, setEditableInfo] = React.useState({
    firstName: student.firstName,
    lastName: student.lastName,
    rfidUid: student.rfidUid || "",
    classGroup: student.classGroup
  });
  const [hasChanges, setHasChanges] = React.useState(false);
  const [classPopoverOpen, setClassPopoverOpen] = React.useState(false);

  // Réinitialiser les données quand l'étudiant change
  React.useEffect(() => {
    setEditableInfo({
      firstName: student.firstName,
      lastName: student.lastName,
      rfidUid: student.rfidUid || "",
      classGroup: student.classGroup
    });
    setHasChanges(false);
  }, [student]);

  // Détecter les changements
  React.useEffect(() => {
    const changed = 
      editableInfo.firstName !== student.firstName ||
      editableInfo.lastName !== student.lastName ||
      editableInfo.rfidUid !== (student.rfidUid || "") ||
      editableInfo.classGroup !== student.classGroup;
    
    setHasChanges(changed);
  }, [editableInfo, student]);
  const handleSave = async () => {
    // Validation: RFID obligatoire
    if (!editableInfo.rfidUid.trim()) {
      return;
    }
    
    try {
      await onUpdateStudent({
        firstName: editableInfo.firstName,
        lastName: editableInfo.lastName,
        rfidUid: editableInfo.rfidUid || null,
        classGroup: editableInfo.classGroup
      });
      setHasChanges(false);
    } catch (error) {
    //   console.error("Erreur lors de la sauvegarde:", error);
    }
  };

  const handleReset = () => {
    setEditableInfo({
      firstName: student.firstName,
      lastName: student.lastName,
      rfidUid: student.rfidUid || "",
      classGroup: student.classGroup
    });
    setHasChanges(false);
  };

  return (
    <Card className="h-fit">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center space-x-2">
            <User className="h-5 w-5 text-blue-600" />
            <span>Informations de l'apprenant</span>
          </span>
          
          {hasChanges && (
            <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
              Modifications non sauvées
            </Badge>
          )}
        </CardTitle>
      </CardHeader>        
      <CardContent className="space-y-4">
        {/* Numéro RFID et Matricule */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 flex items-center space-x-1">
              <CreditCard className="h-4 w-4 text-red-500" />
              <span>Carte RFID *</span>
            </label>
            <RfidUidInput
              value={editableInfo.rfidUid}
              onChange={(value) => setEditableInfo(prev => ({ ...prev, rfidUid: value }))}
              placeholder="AB12CDEF"
              disabled={isLoading}
              className={!editableInfo.rfidUid ? "border-red-300 focus:border-red-500" : ""}
              required
            />
            {!editableInfo.rfidUid && (
              <p className="text-xs text-red-500 mt-1">
                L'UID RFID est obligatoire
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Matricule
            </label>
            <Input
              value={student.id}
              disabled
              className="bg-gray-50 font-mono"
            />
          </div>
        </div>
        {/* Prénom et Nom sur la même ligne */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prénom
            </label>
            <Input
              value={editableInfo.firstName}
              onChange={(e) => setEditableInfo(prev => ({ ...prev, firstName: e.target.value }))}
              placeholder="Prénom"
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom de famille
            </label>
            <Input
              value={editableInfo.lastName}
              onChange={(e) => setEditableInfo(prev => ({ ...prev, lastName: e.target.value }))}
              placeholder="Nom de famille"
              disabled={isLoading}
            />
          </div>
        </div>        
        {/* Classe */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Classe
          </label>
          <Popover open={classPopoverOpen} onOpenChange={setClassPopoverOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={classPopoverOpen}
                className={cn(
                  "w-full justify-between h-10",
                  !editableInfo.classGroup && "text-muted-foreground"
                )}
                disabled={isLoading}              >
                {editableInfo.classGroup
                  ? classGroups.find(
                      (cls) => cls.toLowerCase() === editableInfo.classGroup.toLowerCase()
                    ) || editableInfo.classGroup
                  : "Sélectionner ou créer une classe"}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
              <Command shouldFilter={false}>
                <CommandInput
                  placeholder="Rechercher ou créer..."                  
                  onValueChange={(searchValue) => {
                    if (!classGroups.some(cls => cls.toLowerCase() === searchValue.toLowerCase())) {
                      setEditableInfo(prev => ({ ...prev, classGroup: searchValue }));
                    }
                  }}
                  value={editableInfo.classGroup || ""}
                />
                <CommandList>                  
                  <CommandEmpty>
                    {editableInfo.classGroup && !classGroups.some(cls => cls.toLowerCase() === editableInfo.classGroup.toLowerCase())
                      ? `Créer "${editableInfo.classGroup}"`
                      : "Aucune classe trouvée."}
                  </CommandEmpty>                  <CommandGroup>
                    {classGroups.map((cls) => (
                      <CommandItem
                        value={cls}
                        key={cls}
                        onSelect={(currentValue) => {
                          setEditableInfo(prev => ({ 
                            ...prev, 
                            classGroup: currentValue === editableInfo.classGroup ? "" : currentValue 
                          }));
                          setClassPopoverOpen(false);
                        }}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            editableInfo.classGroup && editableInfo.classGroup.toLowerCase() === cls.toLowerCase()
                              ? "opacity-100"
                              : "opacity-0"
                          )}
                        />
                        {cls}
                      </CommandItem>
                    ))}
                    {editableInfo.classGroup && !classGroups.some(cls => cls.toLowerCase() === editableInfo.classGroup.toLowerCase()) && (
                      <CommandItem
                        value={editableInfo.classGroup}
                        key={`create-${editableInfo.classGroup}`}
                        onSelect={() => {
                          setClassPopoverOpen(false);
                        }}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Créer "{editableInfo.classGroup}"
                      </CommandItem>
                    )}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>

        {/* Actions */}
        {hasChanges && (
          <div className="flex space-x-2 pt-4 border-t">
            <Button
              onClick={handleSave}
              disabled={isLoading || !editableInfo.rfidUid.trim()}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              size="sm"
            >
              <Save className="h-4 w-4 mr-1" />
              Sauvegarder
            </Button>
            
            <Button
              onClick={handleReset}
              disabled={isLoading}
              variant="outline"
              size="sm"
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Annuler
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default StudentInfoPanel;
