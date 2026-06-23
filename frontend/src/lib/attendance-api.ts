import { apiClient } from "./api";

export type AttendanceStatus = "present" | "absent" | "late";

export interface StudentBrief {
  id: string;
  full_name: string;
  email: string;
  year_of_study: number | null;
}

export interface AttendanceRecord {
  id: number;
  student_id: string;
  department_id: string | null;
  year_of_study: number | null;
  subject: string;
  attend_date: string;
  status: string;
  created_at: string;
}

export interface AttendanceSummary {
  total: number;
  present: number;
  absent: number;
  late: number;
  percentage: number;
  records: AttendanceRecord[];
}

export type RiskStatus = "safe" | "warning" | "critical";

export interface SubjectPrediction {
  subject: string;
  present: number;
  total: number;
  percentage: number;
  status: RiskStatus;
  can_miss: number;
  must_attend: number;
  recoverable: boolean;
  message: string;
}

export interface AttendancePrediction {
  threshold: number;
  overall_percentage: number;
  overall_status: RiskStatus;
  at_risk_count: number;
  subjects: SubjectPrediction[];
  summary: string;
}

export interface MarkItem {
  student_id: string;
  status: AttendanceStatus;
}

export async function listStudents(
  departmentId: string,
  year?: number
): Promise<StudentBrief[]> {
  const params = new URLSearchParams({ department_id: departmentId });
  if (year) params.append("year_of_study", String(year));
  const res = await apiClient.get<StudentBrief[]>(
    `/attendance/students?${params.toString()}`
  );
  return res.data;
}

export async function markAttendance(payload: {
  department_id: string;
  year_of_study?: number | null;
  subject: string;
  attend_date: string;
  records: MarkItem[];
}): Promise<{ success: boolean; message: string; saved: number }> {
  const res = await apiClient.post("/attendance/mark", payload);
  return res.data;
}

export async function getMyAttendance(): Promise<AttendanceSummary> {
  const res = await apiClient.get<AttendanceSummary>("/attendance/me");
  return res.data;
}

export async function getAttendancePrediction(): Promise<AttendancePrediction> {
  const res = await apiClient.get<AttendancePrediction>("/attendance/predict");
  return res.data;
}
