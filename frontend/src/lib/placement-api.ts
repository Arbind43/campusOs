import { apiClient } from "./api";

export interface PlacementDrive {
  id: string;
  company_name: string;
  job_role: string;
  package_lpa: number | null;
  drive_date: string | null;
  registration_deadline: string | null;
  description: string;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
}

export interface PlacementDriveCreate {
  company_name: string;
  job_role: string;
  package_lpa?: number | null;
  drive_date?: string | null;
  registration_deadline?: string | null;
  description?: string;
}

export interface PlacementNotice {
  id: number;
  title: string;
  body: string;
  drive_id: string | null;
  created_by: string | null;
  created_at: string;
}

export async function listDrives(activeOnly = true): Promise<PlacementDrive[]> {
  const res = await apiClient.get<PlacementDrive[]>(
    `/placement/drives?active_only=${activeOnly}`
  );
  return res.data;
}

export async function createDrive(body: PlacementDriveCreate): Promise<PlacementDrive> {
  const res = await apiClient.post<PlacementDrive>("/placement/drives", body);
  return res.data;
}

export async function deleteDrive(id: string): Promise<void> {
  await apiClient.delete(`/placement/drives/${id}`);
}

export async function registerForDrive(id: string): Promise<{ message: string }> {
  const res = await apiClient.post<{ message: string }>(`/placement/drives/${id}/register`, {});
  return res.data;
}

export async function listPlacementNotices(): Promise<PlacementNotice[]> {
  const res = await apiClient.get<PlacementNotice[]>("/placement/notices");
  return res.data;
}

export async function createPlacementNotice(body: {
  title: string;
  body: string;
  drive_id?: string | null;
}): Promise<PlacementNotice> {
  const res = await apiClient.post<PlacementNotice>("/placement/notices", body);
  return res.data;
}

export async function deletePlacementNotice(id: number): Promise<void> {
  await apiClient.delete(`/placement/notices/${id}`);
}
