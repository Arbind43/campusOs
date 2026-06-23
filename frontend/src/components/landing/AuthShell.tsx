"use client";

import { ArrowLeft } from "lucide-react";
import Starfield from "@/components/landing/Starfield";

/**
 * Shared dark "Amazon" themed frame for auth screens (login / register / demo).
 * Renders the navy gradient + starfield background and a centered glass card.
 */
export default function AuthShell({
  title,
  subtitle,
  onBack,
  children,
  maxWidth = "max-w-md",
}: {
  title: string;
  subtitle?: string;
  onBack: () => void;
  children: React.ReactNode;
  maxWidth?: string;
}) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0d141d] px-4 py-10 text-white">
      {/* Background layers */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(1000px 500px at 50% -10%, rgba(255,153,0,0.14), transparent 60%), linear-gradient(180deg, #131921 0%, #0d141d 55%, #0a1018 100%)",
        }}
      />
      <Starfield count={50} />

      {/* Back to home */}
      <button
        onClick={onBack}
        className="absolute left-4 top-4 z-10 inline-flex items-center gap-1.5 rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm font-medium text-white/80 backdrop-blur transition hover:border-[#ff9900]/50 hover:text-white sm:left-6 sm:top-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Home
      </button>

      {/* Card */}
      <div
        className={`relative z-10 w-full ${maxWidth} rounded-2xl border border-white/10 bg-white/[0.05] p-7 shadow-2xl shadow-black/40 backdrop-blur-xl sm:p-8`}
      >
        {/* Brand */}
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex items-center gap-2 text-xl font-bold tracking-tight">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-b from-[#febd69] to-[#ff9900] text-base font-black text-[#131921]">
              C
            </span>
            Campus<span className="-ml-1 text-[#ff9900]">OS</span>
          </div>
          <h1 className="text-2xl font-bold">{title}</h1>
          {subtitle && (
            <p className="mt-1 text-sm text-white/55">{subtitle}</p>
          )}
        </div>

        {children}
      </div>
    </main>
  );
}
