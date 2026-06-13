import {
    useQuery,
    useMutation,
    useQueryClient
    // UseMutationOptions // Non utilisé directement
  } from "@tanstack/react-query";
  import { studentsApi } from "@/services/api/students";
  import { StudentBase, StudentUpdate, StudentRead, StudentsPage, StudentOperationResponse } from "@/types/studentTypes";
  // On typiquement veut pouvoir filtrer, donc on accepte un objet "params"
  export interface UseStudentsParams {
    page?: number;
    search?: string;
    classGroup?: string;
    limit?: number;
  }
  
  interface StudentMutationContext {
    previousData?: StudentsPage;
  }
  
  export function useStudents(params?: UseStudentsParams) {
    const qc = useQueryClient();
  
    const queryKey = ["students", params];
  
    // Query pour récupérer la page d'étudiants
    const query = useQuery<StudentsPage, Error>({
      queryKey,
      queryFn: () =>
        studentsApi.getAll(params).then((res) => res.data), // res.data est de type StudentsPage
    });
  
    // Mutation pour créer un étudiant
    const create = useMutation<
      StudentOperationResponse, // L'API retourne StudentOperationResponse
      Error,                    // Type de l'erreur
      StudentBase,              // Type des variables de mutation (ce qu'on envoie)
      StudentMutationContext    // Type du contexte (pour onMutate, onError, onSettled)
    >({
      mutationFn: (data: StudentBase) =>
        studentsApi.create(data).then((res) => res.data), // `res.data` est `StudentOperationResponse`
  
      onMutate: async (newStudent) => {
        await qc.cancelQueries({ queryKey });
        const previousData = qc.getQueryData<StudentsPage>(queryKey);        if (previousData) {
          const tempId = `temp-${Date.now()}`;
          const optimisticStudent: StudentRead = {
            ...newStudent,
            id: tempId, // ID temporaire
            promotion: newStudent.promotion || "", // Assurer que promotion est là
            faceEnrolled: newStudent.faceEnrolled !== undefined ? newStudent.faceEnrolled : false,
            rfidEnrolled: newStudent.rfidEnrolled !== undefined ? newStudent.rfidEnrolled : false,
            rfidScanned: false, // Champ de StudentRead, non dans StudentBase
          };
          qc.setQueryData<StudentsPage>(queryKey, {
            ...previousData,
            items: [...previousData.items, optimisticStudent],
          });
        }
        return { previousData }; 
      },
      onError: (err, newStudent, context) => {
        if (context?.previousData) {
          qc.setQueryData(queryKey, context.previousData);
        }
        // Idéalement, logger l'erreur ou afficher un toast
      },
      onSettled: () => {
        qc.invalidateQueries({ queryKey }); // Ré-fetcher les données après succès ou erreur
      },
    });
  
    // Mutation pour mettre à jour un étudiant
    const update = useMutation<
      StudentRead,              // L'API retourne StudentRead après update
      Error,
      { id: string; data: StudentUpdate },
      StudentMutationContext
    >({
      mutationFn: ({ id, data }) =>
        studentsApi.update(id, data).then((res) => res.data),
  
      onMutate: async ({ id, data }) => {
        await qc.cancelQueries({ queryKey });
        const previousData = qc.getQueryData<StudentsPage>(queryKey);
        if (previousData) {
          qc.setQueryData<StudentsPage>(queryKey, {
            ...previousData,
            items: previousData.items.map((s) =>
              s.id === id ? { ...s, ...data } as StudentRead : s
            ),
          });
        }
        return { previousData };
      },
      onError: (err, variables, context) => {
        if (context?.previousData) {
          qc.setQueryData(queryKey, context.previousData);
        }
      },
      onSettled: () => {
        qc.invalidateQueries({ queryKey });
      },
    });
  
    // Mutation pour supprimer un étudiant
    const remove = useMutation<
      void,                     // L'API retourne void (Promise<void>)
      Error,
      string,                   // L'ID de l'étudiant à supprimer
      StudentMutationContext
    >({
      mutationFn: (id: string) => studentsApi.remove(id),
      onMutate: async (id) => {
        await qc.cancelQueries({ queryKey });
        const previousData = qc.getQueryData<StudentsPage>(queryKey);
        if (previousData) {
          qc.setQueryData<StudentsPage>(queryKey, {
            ...previousData,
            items: previousData.items.filter((s) => s.id !== id),
          });
        }
        return { previousData };
      },
      onError: (err, id, context) => {
        if (context?.previousData) {
          qc.setQueryData(queryKey, context.previousData);
        }
      },
      onSettled: () => {
        qc.invalidateQueries({ queryKey });
      },
    });
  
    // Exposer query.data directement sous le nom `studentsPage` pour plus de clarté
    return { studentsPage: query.data, 
                isLoading: query.isLoading, 
                isError: query.isError, 
                error: query.error, 
                refetch: query.refetch, 
                create, 
                update, 
                remove };
  }
  