import { apiClient } from "./api";

export interface WellbeingStatus {
  submitted: boolean;
  week_start: string;
}

export interface WellbeingCheckin {
  mood: number;
  stress: number;
  sleep: number;
  note?: string | null;
}

export interface DeptStat {
  department: string;
  responses: number;
  avg_stress: number;
  high_stress_pct: number;
}

export interface WeekPoint {
  week_start: string;
  responses: number;
  avg_mood: number;
  avg_stress: number;
  avg_sleep: number;
  high_stress_pct: number;
}

export interface WellbeingInsights {
  week_start: string;
  responses: number;
  avg_mood: number;
  avg_stress: number;
  avg_sleep: number;
  high_stress_pct: number;
  low_mood_pct: number;
  status: "calm" | "watch" | "elevated";
  insight: string;
  recommendations: string[];
  departments: DeptStat[];
  trend: WeekPoint[];
  min_cohort: number;
}

export async function getCheckinStatus(): Promise<WellbeingStatus> {
  const res = await apiClient.get<WellbeingStatus>("/wellbeing/status");
  return res.data;
}

export async function submitCheckin(body: WellbeingCheckin): Promise<WellbeingStatus> {
  const res = await apiClient.post<WellbeingStatus>("/wellbeing/checkin", body);
  return res.data;
}

export async function getInsights(): Promise<WellbeingInsights> {
  const res = await apiClient.get<WellbeingInsights>("/wellbeing/insights");
  return res.data;
}
