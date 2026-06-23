"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/auth-api";
import { getErrorMessage } from "@/lib/api";
import { CheckCircle2 } from "lucide-react";
import { Suspense } from 'react';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token. Please request a new password reset link.");
    }
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      await authApi.resetPassword(token, password);
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="flex flex-col items-center space-y-4 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
          <CheckCircle2 className="h-6 w-6 text-green-500" />
        </div>
        <div>
          <h3 className="mb-1 text-lg font-medium text-white">Password Reset Successfully</h3>
          <p className="text-sm text-white/60">
            Your password has been changed. You can now use your new password to log in.
          </p>
        </div>
        <button
          onClick={() => router.push("/")}
          className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-white/10 py-2.5 text-sm font-semibold text-white hover:bg-white/20 transition"
        >
          Return to Login
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="password" className="text-white/80">
          New Password
        </Label>
        <Input
          id="password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="confirm-password" className="text-white/80">
          Confirm New Password
        </Label>
        <Input
          id="confirm-password"
          type="password"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          className="border-white/15 bg-white/5 text-white placeholder:text-white/35 focus-visible:ring-[#ff9900] focus-visible:ring-offset-0"
        />
      </div>

      {error && (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading || !token}
        className="inline-flex w-full items-center justify-center rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] py-2.5 text-sm font-semibold text-[#131921] shadow-lg shadow-[#ff9900]/25 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Resetting..." : "Reset Password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0f1115]">
      <div className="w-full max-w-[400px] px-4">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-b from-[#febd69] to-[#ff9900] shadow-lg shadow-[#ff9900]/20">
            <svg
              className="h-6 w-6 text-[#131921]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h1 className="mb-2 text-2xl font-bold tracking-tight text-white">
            Create New Password
          </h1>
          <p className="text-sm text-white/60">
            Please enter your new password below.
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#131921]/80 p-6 shadow-2xl backdrop-blur-xl md:p-8">
          <Suspense fallback={<div className="text-center text-white/60 py-4">Loading...</div>}>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
