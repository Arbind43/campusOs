import axios, { AxiosError, type AxiosInstance } from "axios";
import { useAuthStore } from "@/store/auth";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://campusos-ifab.onrender.com/api/v1";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Attach JWT token on every request
apiClient.interceptors.request.use(async (config) => {
  const auth = useAuthStore.getState();
  const token = auth.token;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // For FormData (file uploads), let browser set Content-Type with boundary
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }

  return config;
});

// On 401, clear local auth state
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const state = useAuthStore.getState();
      state.clearAuth();
    }
    return Promise.reject(error);
  }
);

/** Extract a user-friendly message from any Axios error. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string | { msg: string }[] }
      | undefined;

    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d) => d.msg).join(". ");
    }
    if (error.code === "ECONNABORTED") return "Request timed out. Please try again.";
    if (error.message) return error.message;
  }
  return "Something went wrong. Please try again.";
}
