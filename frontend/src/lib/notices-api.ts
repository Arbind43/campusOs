import { apiClient } from "./api";

export interface Notice {
  id: string;
  title: string;
  body: string;
  domain: string;
  target_department_id: string | null;
  target_year: number | null;
  created_by: string | null;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface NoticeCreate {
  title: string;
  body: string;
  domain: "academic" | "hostel" | "placement" | "clubs" | "general";
  target_department_id?: string | null;
  target_year?: number | null;
  is_pinned?: boolean;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  created_at: string;
}

export async function listNotices(domain?: string): Promise<Notice[]> {
  const params = new URLSearchParams();
  if (domain) params.append("domain", domain);
  const res = await apiClient.get<Notice[]>(`/notices?${params.toString()}`);
  return res.data;
}

export async function createNotice(body: NoticeCreate): Promise<Notice> {
  const res = await apiClient.post<Notice>("/notices", body);
  return res.data;
}

export async function deleteNotice(id: string): Promise<void> {
  await apiClient.delete(`/notices/${id}`);
}

export async function listDepartments(): Promise<Department[]> {
  const res = await apiClient.get<Department[]>("/academic/departments");
  return res.data;
}
