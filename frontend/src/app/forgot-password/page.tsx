"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/auth-api";
import { getErrorMessage } from "@/lib/api";
import { ArrowLeft, CheckCircle2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await authApi.forgotPassword(email);
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

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
                d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
              />
            </svg>
          </div>
          <h1 className="mb-2 text-2xl font-bold tracking-tight text-white">
            Reset Password
          </h1>
          <p className="text-sm text-white/60">
            Enter your email to receive a password reset link.
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#131921]/80 p-6 shadow-2xl backdrop-blur-xl md:p-8">
          {success ? (
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <h3 className="mb-1 text-lg font-medium text-white">Check your email</h3>
                <p className="text-sm text-white/60">
                  If an account exists for {email}, we have sent a password reset link.
                </p>
                <div className="mt-4 p-4 bg-white/5 border border-white/10 rounded-lg text-xs text-white/40 text-left">
                  <p className="font-semibold text-white/70 mb-1">Dev Mode Notice:</p>
                  <p>In dev mode, no email is actually sent.</p>
                  <button 
                    onClick={() => router.push(`/reset-password?token=dev-token-123`)}
                    className="mt-2 text-[#ff9900] hover:underline cursor-pointer"
                  >
                    Click here to simulate clicking the email link
                  </button>
                </div>
              </div>
              <button
                onClick={() => router.push("/")}
                className="mt-6 text-sm font-medium text-[#ff9900] hover:underline"
              >
                Return to Login
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-white/80">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="admin@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
                disabled={loading}
                className="inline-flex w-full items-center justify-center rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] py-2.5 text-sm font-semibold text-[#131921] shadow-lg shadow-[#ff9900]/25 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>
          )}
        </div>

        {!success && (
          <div className="mt-6 flex justify-center">
            <button
              onClick={() => router.push("/")}
              className="inline-flex items-center text-sm font-medium text-white/60 hover:text-white transition-colors"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
