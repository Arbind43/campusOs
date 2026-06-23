import { apiClient } from "./api";
import { Department } from "./notices-api";

export interface ManagedUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_demo: boolean;
  department_id: string | null;
  year_of_study: number | null;
  hostel_room_id: string | null;
  roles: string[];
}

export interface UserUpdate {
  department_id?: string | null;
  year_of_study?: number | null;
  role?: string;
}

export async function listManagedUsers(params?: {
  role?: string;
  departmentId?: string;
}): Promise<ManagedUser[]> {
  const q = new URLSearchParams();
  if (params?.role) q.append("role", params.role);
  if (params?.departmentId) q.append("department_id", params.departmentId);
  const res = await apiClient.get<ManagedUser[]>(`/admin/manage/users?${q.toString()}`);
  return res.data;
}

export async function updateManagedUser(
  userId: string,
  body: UserUpdate
): Promise<ManagedUser> {
  const res = await apiClient.patch<ManagedUser>(`/admin/manage/users/${userId}`, body);
  return res.data;
}

export async function createDepartment(
  name: string,
  code: string
): Promise<Department> {
  const res = await apiClient.post<Department>("/admin/manage/departments", {
    name,
    code,
  });
  return res.data;
}
