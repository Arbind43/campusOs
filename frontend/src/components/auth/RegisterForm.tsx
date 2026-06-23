"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/auth-api";
import { useAuthStore } from "@/store/auth";
import { getErrorMessage } from "@/lib/api";

type RegisterRole = "student" | "professor" | "admin";

const REGISTER_ROLES: { value: RegisterRole; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "professor", label: "Professor" },
  { value: "admin", label: "Admin" },
];

export default function RegisterForm() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const setUser = useAuthStore((s) => s.setUser);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<RegisterRole>("student");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) return;

    setError(null);
    setLoading(true);

    try {
      const res = await authApi.register({ email, password, full_name: fullName, role });
      setToken(res.data.access_token);
      setUser(res.data.user);
      router.push("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="reg-name" className="text-white/80">
          Full Name
        </Label>
        <Input
          id="reg-name"
          type="text"
          placeholder="Bikram Sharma"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          autoComplete="name"
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="reg-email" className="text-white/80">
          Email
        </Label>
        <Input
          id="reg-email"
          type="email"
          placeholder="you@university.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="reg-password" className="text-white/80">
          Password
        </Label>
        <Input
          id="reg-password"
          type="password"
          placeholder="Minimum 8 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
          minLength={8}
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>

      <div className="space-y-2">
        <Label className="text-white/80">I am a</Label>
        <div className="flex gap-2">
          {REGISTER_ROLES.map((r) => (
            <button
              key={r.value}
              type="button"
              onClick={() => setRole(r.value)}
              className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium capitalize transition ${
                role === r.value
                  ? "border-[#ff9900] bg-[#ff9900]/15 text-[#febd69]"
                  : "border-white/15 bg-white/5 text-white/70 hover:border-white/30 hover:text-white"
              }`}
              aria-pressed={role === r.value}
            >
              {r.label}
            </button>
          ))}
        </div>
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
        {loading ? "Creating account…" : "Create Account"}
      </button>
    </form>
  );
}
