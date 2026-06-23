import { apiClient } from "./api";

export interface TimetableEntry {
  id: number;
  department_id: string;
  semester: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  subject: string;
  room: string | null;
  faculty_name: string | null;
  created_at: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  extracted_text: string;
  entries_created: number;
  entries: TimetableEntry[];
  errors: string[];
}

export async function uploadTimetable(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<UploadResponse>(
    "/academic/timetable/upload",
    formData
    // Don't set Content-Type header - axios will set it with boundary
  );

  return response.data;
}

export async function confirmTimetable(entries: TimetableEntry[]): Promise<UploadResponse> {
  const response = await apiClient.post<UploadResponse>(
    "/academic/timetable/confirm",
    { entries }
  );

  return response.data;
}

export async function getTimetable(
  departmentId?: string,
  semester?: number
): Promise<TimetableEntry[]> {
  const params = new URLSearchParams();
  if (departmentId) params.append("department_id", departmentId);
  if (semester) params.append("semester", semester.toString());

  const response = await apiClient.get<TimetableEntry[]>(
    `/academic/timetable?${params.toString()}`
  );

  return response.data;
}
