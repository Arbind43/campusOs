import { apiClient } from "./api";
import type { UserProfile } from "@/store/auth";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role?: "student" | "professor" | "admin";
}

export const authApi = {
  /** Login with email and password - returns token and user profile */
  login: (payload: LoginPayload) =>
    apiClient.post<LoginResponse>("/auth/login", payload),

  /** Register a new user */
  register: (payload: RegisterPayload) =>
    apiClient.post<LoginResponse>("/auth/register", payload),

  /** Returns the current user's profile from our DB */
  me: () => apiClient.get<UserProfile>("/auth/me"),
  forgotPassword: (email: string) => 
    apiClient.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, password: string) => 
    apiClient.post("/auth/reset-password", { token, password }),
};
