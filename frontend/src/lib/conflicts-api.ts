import { apiClient } from "./api";

export type ConflictType =
  | "exam_room"
  | "exam_student_overlap"
  | "class_room"
  | "class_faculty"
  | "event_venue";

export interface ScheduleConflict {
  type: ConflictType;
  severity: "high" | "medium" | "low";
  title: string;
  detail: string;
  when: string;
  items: string[];
}

export interface ConflictScanResult {
  scanned_at: string;
  total: number;
  counts: Record<string, number>;
  conflicts: ScheduleConflict[];
}

export async function scanConflicts(): Promise<ConflictScanResult> {
  const res = await apiClient.get<ConflictScanResult>("/academic/conflicts");
  return res.data;
}

/* ── Conflict-aware class scheduling ──────────────────────────────────────── */

export interface ClassSlot {
  department_id: string;
  semester: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  subject: string;
  room?: string | null;
  faculty_name?: string | null;
}

export interface SlotConflict {
  kind: "room" | "faculty" | "cohort";
  detail: string;
}

export interface SlotCheckResult {
  has_conflict: boolean;
  conflicts: SlotConflict[];
}

export async function checkSlot(slot: ClassSlot): Promise<SlotCheckResult> {
  const res = await apiClient.post<SlotCheckResult>("/academic/timetable/check", slot);
  return res.data;
}

export async function scheduleClass(slot: ClassSlot): Promise<void> {
  await apiClient.post("/academic/timetable", slot);
}

export interface FreeWindow {
  start: string;
  end: string;
}

export interface RoomFreeSlots {
  room: string;
  free_windows: FreeWindow[];
}

export interface FreeSlotsResult {
  day_of_week: string;
  working_start: string;
  working_end: string;
  rooms: RoomFreeSlots[];
}

export async function getFreeSlots(day: string): Promise<FreeSlotsResult> {
  const res = await apiClient.get<FreeSlotsResult>(
    `/academic/free-slots?day_of_week=${encodeURIComponent(day)}`
  );
  return res.data;
}
