"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";
import { authApi } from "@/lib/auth-api";

/**
 * Validates the stored token on mount and fetches user profile.
 * Mount once in the root layout.
 */
export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { token, setUser, clearAuth } = useAuthStore();

  useEffect(() => {
    // If we have a token, validate it by fetching the user profile
    if (token) {
      authApi
        .me()
        .then((res) => setUser(res.data))
        .catch((err) => {
          console.error("Token validation failed:", err);
          // Token is invalid or expired, clear auth
          clearAuth();
        });
    }
  }, []); // Only run on mount

  return <>{children}</>;
}
