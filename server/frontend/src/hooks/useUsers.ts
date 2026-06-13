import {
  useQuery,
  useMutation,
  useQueryClient
} from "@tanstack/react-query";
import { userApi, CreateUserPayload } from "@/services/api/user";
import { User } from "@/types/userTypes";

export interface UseUsersParams {
  search?: string;
}

interface UserMutationContext {
  previousData?: User[];
}

export function useUsers(params?: UseUsersParams) {
  const qc = useQueryClient();

  const queryKey = ["users", params];

  // Query pour récupérer la liste des utilisateurs
  const query = useQuery<User[], Error>({
    queryKey,
    queryFn: () => userApi.getUsers(),
  });

  // Mutation pour créer un utilisateur
  const create = useMutation<
    User,                     // L'API retourne User après création
    Error,                    // Type de l'erreur
    CreateUserPayload,        // Type des variables de mutation (ce qu'on envoie)
    UserMutationContext       // Type du contexte
  >({
    mutationFn: (data: CreateUserPayload) => userApi.createUser(data),

    onMutate: async (newUser) => {
      await qc.cancelQueries({ queryKey });
      const previousData = qc.getQueryData<User[]>(queryKey);      if (previousData) {
        const tempId = Date.now(); // ID temporaire numérique
        const optimisticUser: User = {
          ...newUser,
          id: tempId,
        };
        qc.setQueryData<User[]>(queryKey, [...previousData, optimisticUser]);
      }
      return { previousData };
    },
    onError: (err, newUser, context) => {
      if (context?.previousData) {
        qc.setQueryData(queryKey, context.previousData);
      }
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey });
    },
  });
  // Mutation pour mettre à jour un utilisateur
  const update = useMutation<
    User,                     // L'API retourne User après update
    Error,
    { id: number; data: Partial<CreateUserPayload> },
    UserMutationContext
  >({
    mutationFn: ({ id, data }) => userApi.updateUser(id.toString(), data),    onMutate: async ({ id, data }) => {
      await qc.cancelQueries({ queryKey });
      const previousData = qc.getQueryData<User[]>(queryKey);
      if (previousData) {
        qc.setQueryData<User[]>(queryKey,
          previousData.map((user) =>
            user.id === id ? { ...user, ...data } as User : user
          )
        );
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
  // Mutation pour supprimer un utilisateur
  const remove = useMutation<
    void,                     // L'API retourne void
    Error,
    number,                   // L'ID de l'utilisateur à supprimer
    UserMutationContext
  >({
    mutationFn: (id: number) => userApi.deleteUser(id.toString()),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey });
      const previousData = qc.getQueryData<User[]>(queryKey);
      if (previousData) {
        qc.setQueryData<User[]>(queryKey,
          previousData.filter((user) => user.id !== id)
        );
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

  return {
    users: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    create,
    update,
    remove
  };
}
