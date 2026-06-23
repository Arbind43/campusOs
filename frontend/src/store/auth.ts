import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Role = "STUDENT" | "ACADEMIC_ADMIN" | "SUPER_ADMIN" | "FACULTY";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_demo: boolean;
  department_id?: string | null;
  year_of_study?: number | null;
  hostel_room_id?: string | null;
  roles?: string[];
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  setToken: (token: string) => void;
  setUser: (user: UserProfile) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),

      clearAuth: () => set({ token: null, user: null }),

      isAuthenticated: () => get().token !== null && get().user !== null,
    }),
    {
      name: "auth-storage", // localStorage key
    }
  )
);
