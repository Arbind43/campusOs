import { apiClient } from "./api";

export interface AIResponse {
  reply: string;
  context_used: string[];
}

export interface ChatMessageRecord {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export async function askAssistant(message: string): Promise<AIResponse> {
  const res = await apiClient.post<AIResponse>("/ai/query", { message });
  return res.data;
}

export async function getChatHistory(): Promise<ChatMessageRecord[]> {
  const res = await apiClient.get<ChatMessageRecord[]>("/ai/history");
  return res.data;
}

export async function clearChatHistory(): Promise<void> {
  await apiClient.delete("/ai/history");
}
