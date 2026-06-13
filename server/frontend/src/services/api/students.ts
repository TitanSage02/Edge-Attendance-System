import { api } from "../api";
import { StudentBase, StudentUpdate, StudentRead, StudentOperationResponse, StudentsPage } from "@/types/studentTypes";
import { UseStudentsParams } from "@/hooks/useStudents";

export const studentsApi = {
  // getAll: (skip = 0, limit = 100) => api.get<StudentBase[]>(`/students?skip=${skip}&limit=${limit}`),
  getAll: (params?: UseStudentsParams) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.classGroup && params.classGroup !== "all") queryParams.append('classGroup', params.classGroup);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
   
    return api.get<StudentsPage>(`/students/${query}`);
  },
  getStudents: async () => {
    const response = await api.get<StudentsPage>('/students/?limit=100');
    return response.data.items;
  },
  getOne: (id: string) => api.get<StudentRead>(`/students/${id}`),
  create: (data: StudentBase) => api.post<StudentOperationResponse>(`/students/`, data),
  update: (id: string, data: StudentUpdate) => api.patch<StudentRead>(`/students/${id}`, data),
  remove: async (id: string): Promise<void> => {
    await api.delete<void>(`/students/${id}`);
  },
};