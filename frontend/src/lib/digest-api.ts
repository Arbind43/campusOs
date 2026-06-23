import { apiClient } from "./api";

export interface DigestClass {
  subject: string;
  start: string;
  end: string;
  room: string | null;
  at_risk: boolean;
}

export interface DigestItem {
  title: string;
  subtitle: string | null;
  when: string | null;
  urgent: boolean;
}

export interface DigestResponse {
  greeting: string;
  date: string;
  insight: string;
  classes: DigestClass[];
  assignments: DigestItem[];
  deadlines: DigestItem[];
  notices: DigestItem[];
  events: DigestItem[];
  attendance_alerts: DigestItem[];
  quick_actions: string[];
}

export async function getDigest(): Promise<DigestResponse> {
  const res = await apiClient.get<DigestResponse>("/ai/digest");
  return res.data;
}
