"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/auth-api";
import { useAuthStore } from "@/store/auth";
import { getErrorMessage } from "@/lib/api";

export default function LoginForm() {
  const router = useRouter();
  const { setUser, setToken } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Call the new backend login endpoint
      const response = await authApi.login({ email, password });
      const { access_token, user } = response.data;

      // Store token and user in auth store
      setToken(access_token);
      setUser(user);

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="login-email" className="text-white/80">
          Email
        </Label>
        <Input
          id="login-email"
          type="email"
          placeholder="admin@college.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="login-password" className="text-white/80">
            Password
          </Label>
          <button
            type="button"
            onClick={() => router.push("/forgot-password")}
            className="text-xs font-medium text-[#ff9900] hover:underline"
          >
            Forgot Password?
          </button>
        </div>
        <Input
          id="login-password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300"
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="inline-flex w-full items-center justify-center rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] py-2.5 text-sm font-semibold text-[#131921] shadow-lg shadow-[#ff9900]/25 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Signing in…" : "Sign In"}
      </button>

      <p className="mt-2 text-center text-xs text-white/40">
        Dev mode: any password works. Try admin@college.edu
      </p>
    </form>
  );
}
