"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, CalendarDays, Megaphone, PartyPopper, Sunrise, ArrowRight, UserRound } from "lucide-react";
import LoginForm from "@/components/auth/LoginForm";
import RegisterForm from "@/components/auth/RegisterForm";
import { supabase } from "@/lib/supabase";
import Starfield from "@/components/landing/Starfield";
import Globe3D from "@/components/landing/Globe3D";
import AuthShell from "@/components/landing/AuthShell";

type View = "landing" | "login" | "register" | "demo-select";

// Demo accounts with different roles
const DEMO_ACCOUNTS = [
  {
    email: "demo.student@campusos.app",
    password: "demo1234",
    role: "STUDENT",
    name: "Student",
    description: "View timetable, assignments, events",
  },
  {
    email: "demo.admin@campusos.app",
    password: "demo1234",
    role: "ACADEMIC_ADMIN",
    name: "Academic Admin",
    description: "Upload timetables, manage schedules",
  },
  {
    email: "demo.professor@campusos.app",
    password: "demo1234",
    role: "FACULTY",
    name: "Professor",
    description: "Post notices, upload assignments",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [view, setView] = useState<View>("landing");
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [demoError, setDemoError] = useState<string | null>(null);

  async function handleTryDemo(demoAccount: typeof DEMO_ACCOUNTS[0]) {
    setDemoError(null);
    setDemoLoading(demoAccount.email);

    const { error } = await supabase.auth.signInWithPassword({
      email: demoAccount.email,
      password: demoAccount.password,
    });

    if (error) {
      setDemoError(`${demoAccount.name} demo account unavailable. Please try again later.`);
      setDemoLoading(null);
      return;
    }

    router.push("/dashboard");
  }

  if (view === "login") {
    return (
      <AuthShell
        title="Welcome back"
        subtitle="Sign in to continue to CampusOS"
        onBack={() => setView("landing")}
      >
        <LoginForm />
        <p className="mt-6 text-center text-sm text-white/55">
          No account?{" "}
          <button
            onClick={() => setView("register")}
            className="font-semibold text-[#febd69] underline-offset-4 hover:underline"
          >
            Create one
          </button>
        </p>
      </AuthShell>
    );
  }

  if (view === "register") {
    return (
      <AuthShell
        title="Create your account"
        subtitle="Join CampusOS in seconds"
        onBack={() => setView("landing")}
      >
        <RegisterForm />
        <p className="mt-6 text-center text-sm text-white/55">
          Already have an account?{" "}
          <button
            onClick={() => setView("login")}
            className="font-semibold text-[#febd69] underline-offset-4 hover:underline"
          >
            Sign In
          </button>
        </p>
      </AuthShell>
    );
  }

  if (view === "demo-select") {
    return (
      <AuthShell
        title="Try CampusOS"
        subtitle="Pick a role to explore with demo data"
        onBack={() => setView("landing")}
        maxWidth="max-w-3xl"
      >
        <div className="space-y-4">
          {demoError && (
            <div className="flex gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <div>{demoError}</div>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-3">
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                onClick={() => handleTryDemo(account)}
                disabled={demoLoading !== null}
                className="group relative overflow-hidden rounded-xl border border-white/10 bg-white/[0.04] p-4 text-left backdrop-blur transition hover:-translate-y-1 hover:border-[#ff9900]/40 hover:bg-white/[0.07] disabled:opacity-50"
              >
                <div className="space-y-2">
                  <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#ff9900]/15 text-[#ff9900]">
                    <UserRound className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-white group-hover:text-[#febd69]">
                    {account.name}
                  </h3>
                  <p className="text-sm text-white/55">{account.description}</p>
                  <p className="font-mono text-xs text-white/35">
                    {account.email}
                  </p>
                </div>
                {demoLoading === account.email && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                    <div className="text-xs font-medium text-white">
                      Logging in…
                    </div>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </AuthShell>
    );
  }

  const FEATURES = [
    { Icon: CalendarDays, label: "Timetable OCR", desc: "Snap your schedule, we digitize it" },
    { Icon: Megaphone, label: "AI Summaries", desc: "Notices condensed in seconds" },
    { Icon: PartyPopper, label: "Event Reminders", desc: "Never miss what matters" },
    { Icon: Sunrise, label: "Daily Briefing", desc: "Your morning, organized" },
  ];

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0d141d] text-white">
      {/* Background layers */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(1200px 600px at 50% -10%, rgba(255,153,0,0.12), transparent 60%), linear-gradient(180deg, #131921 0%, #0d141d 55%, #0a1018 100%)",
        }}
      />
      <Starfield count={70} />

      {/* Top bar */}
      <header className="relative z-10 px-5 py-4 sm:px-10 sm:py-5">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2 text-xl font-bold tracking-tight sm:text-2xl">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] text-sm font-black text-[#131921] sm:h-8 sm:w-8 sm:text-base">
              C
            </span>
            Campus<span className="-ml-1 text-[#ff9900]">OS</span>
          </div>
          <button
            onClick={() => setView("login")}
            className="inline-flex items-center gap-1.5 rounded-md border border-white/20 bg-white/5 px-3 py-2 text-sm font-medium text-white/90 backdrop-blur transition hover:border-[#ff9900]/50 hover:bg-white/10 hover:text-white sm:px-4"
          >
            <ArrowRight className="h-4 w-4" />
            Sign In
          </button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative z-10 mx-auto flex max-w-6xl flex-col items-center px-5 pt-6 pb-16 text-center sm:px-6 sm:pt-10 sm:pb-20">
        {/* Globe */}
        <div className="relative mb-2 flex w-full max-w-[260px] items-center justify-center sm:mb-6 sm:max-w-[340px]">
          <Globe3D maxSize={340} />
        </div>

        <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#ff9900]/40 bg-[#ff9900]/10 px-3 py-1.5 text-[11px] font-medium text-[#febd69] sm:px-4 sm:text-xs">
          <span className="h-1.5 w-1.5 rounded-full bg-[#ff9900]" />
          Built for modern campuses
        </span>

        <h1 className="max-w-3xl text-3xl font-extrabold leading-tight tracking-tight sm:text-6xl">
          Your AI Operating System
          <br />
          for{" "}
          <span className="bg-gradient-to-r from-[#ff9900] to-[#febd69] bg-clip-text text-transparent">
            Student Life
          </span>
        </h1>

        <p className="mt-4 max-w-xl text-sm text-white/60 sm:mt-5 sm:text-lg">
          Timetables, notices, events, and daily briefings — unified into one
          intelligent platform that works while you focus on what matters.
        </p>

        {/* CTAs */}
        <div className="mt-8 flex w-full flex-col gap-3 sm:mt-9 sm:w-auto sm:flex-row">
          <button
            onClick={() => setView("register")}
            className="group inline-flex items-center justify-center gap-2 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] px-7 py-3 text-sm font-semibold text-[#131921] shadow-lg shadow-[#ff9900]/25 transition hover:brightness-105"
          >
            Get Started
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </button>
          <button
            onClick={() => setView("demo-select")}
            className="inline-flex items-center justify-center rounded-md border border-white/20 bg-white/5 px-7 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/10"
          >
            Try Live Demo
          </button>
        </div>

        {/* Feature cards */}
        <div className="mt-16 grid w-full max-w-4xl grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ Icon, label, desc }) => (
            <div
              key={label}
              className="group rounded-xl border border-white/10 bg-white/[0.04] p-5 text-left backdrop-blur transition hover:-translate-y-1 hover:border-[#ff9900]/40 hover:bg-white/[0.07]"
            >
              <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[#ff9900]/15 text-[#ff9900]">
                <Icon className="h-5 w-5" />
              </div>
              <div className="font-semibold text-white">{label}</div>
              <div className="mt-1 text-sm text-white/50">{desc}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
