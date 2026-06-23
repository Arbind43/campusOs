import { apiClient } from "./api";

export interface MessEntry {
  id?: number;
  day_of_week: string;
  meal_type: string;
  start_time: string | null;
  end_time: string | null;
  items: string;
  is_special: boolean;
}

export interface MessUploadResponse {
  success: boolean;
  message: string;
  extracted_text: string;
  entries: MessEntry[];
  errors: string[];
}

export async function getMess(): Promise<MessEntry[]> {
  const res = await apiClient.get<MessEntry[]>("/mess");
  return res.data;
}

export async function uploadMess(file: File): Promise<MessUploadResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await apiClient.post<MessUploadResponse>("/mess/upload", fd);
  return res.data;
}

export async function confirmMess(entries: MessEntry[]): Promise<MessUploadResponse> {
  const res = await apiClient.post<MessUploadResponse>("/mess/confirm", { entries });
  return res.data;
}

/* ── Mess sentiment loop ──────────────────────────────────────────────────── */

export interface TodayRatings {
  rating_date: string;
  ratings: Record<string, number>;
}

export interface MealSentiment {
  meal_type: string;
  count: number;
  avg: number;
  positive_pct: number;
  negative_pct: number;
}

export interface SentimentTrendPoint {
  day: string;
  count: number;
  avg: number;
}

export interface MessSentiment {
  day: string;
  total: number;
  overall_avg: number;
  meals: MealSentiment[];
  trend: SentimentTrendPoint[];
  alerts: string[];
}

export async function getTodayRatings(): Promise<TodayRatings> {
  const res = await apiClient.get<TodayRatings>("/mess/rate/today");
  return res.data;
}

export async function rateMeal(meal_type: string, rating: number): Promise<TodayRatings> {
  const res = await apiClient.post<TodayRatings>("/mess/rate", { meal_type, rating });
  return res.data;
}

export async function getMessSentiment(): Promise<MessSentiment> {
  const res = await apiClient.get<MessSentiment>("/mess/sentiment");
  return res.data;
}
