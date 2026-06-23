"use client";

import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Calendar,
  Bell,
  BarChart3,
  Upload,
  Users,
  GraduationCap,
  LogOut,
  ArrowRight,
  Sparkles,
  Utensils,
  Bot,
  Briefcase,
  HeartPulse,
  CalendarClock,
  MessageSquare,
} from "lucide-react";
import NotificationBell from "@/components/notifications/NotificationBell";
import DailyDigest from "@/components/dashboard/DailyDigest";

type Feature = {
  icon: typeof Calendar;
  title: string;
  description: string;
  href: string;
  active: boolean;
};

// Student Features
const STUDENT_FEATURES: Feature[] = [
  { icon: Calendar, title: "View Timetable", description: "Check your class schedule", href: "/dashboard/timetable", active: true },
  { icon: BarChart3, title: "Attendance", description: "Track your attendance record", href: "/dashboard/attendance", active: true },
  { icon: Bell, title: "Notices", description: "Important announcements", href: "/dashboard/notices", active: true },
  { icon: Utensils, title: "Mess Menu", description: "Meals & timings for the week", href: "/dashboard/mess", active: true },
  { icon: Briefcase, title: "Placements", description: "Drives & preparation resources", href: "/dashboard/placement", active: true },
  { icon: HeartPulse, title: "Wellbeing Check-in", description: "Anonymous weekly mood check-in", href: "/dashboard/wellbeing", active: true },
  { icon: MessageSquare, title: "Helpdesk", description: "Submit maintenance & IT requests", href: "/dashboard/helpdesk", active: true },
];

// Academic Admin Features
const ADMIN_FEATURES: Feature[] = [
  { icon: Upload, title: "Update Timetable", description: "Upload & manage class schedules via image", href: "/dashboard/timetable", active: true },
  { icon: BarChart3, title: "Attendance Management", description: "Mark & manage student attendance", href: "/dashboard/attendance", active: true },
  { icon: Bell, title: "Create Notices", description: "Announce to students by dept & year", href: "/dashboard/notices", active: true },
  { icon: Utensils, title: "Mess Menu", description: "Upload the campus mess schedule", href: "/dashboard/mess", active: true },
  { icon: Briefcase, title: "Placement Management", description: "Post drives & prep resources", href: "/dashboard/placement", active: true },
  { icon: HeartPulse, title: "Wellbeing Insights", description: "Anonymous mood trends & alerts", href: "/dashboard/wellbeing", active: true },
  { icon: CalendarClock, title: "Schedule a Class", description: "Conflict-free class scheduling", href: "/dashboard/conflicts", active: true },
  { icon: Users, title: "User Management", description: "Assign students to dept & year", href: "/dashboard/users", active: true },
  { icon: MessageSquare, title: "Helpdesk Management", description: "Manage & assign campus tickets", href: "/dashboard/helpdesk", active: true },
];

// Faculty/Professor Features
const FACULTY_FEATURES: Feature[] = [
  { icon: BarChart3, title: "Mark Attendance", description: "Track student attendance", href: "/dashboard/attendance", active: true },
  { icon: Bell, title: "Post Notices", description: "Send announcements to students", href: "/dashboard/notices", active: true },
  { icon: Briefcase, title: "Placements", description: "Drives & preparation resources", href: "/dashboard/placement", active: true },
  { icon: MessageSquare, title: "Helpdesk", description: "Submit maintenance & IT requests", href: "/dashboard/helpdesk", active: true },
  { icon: GraduationCap, title: "Create Classroom", description: "Set up new classroom and sections", href: "#", active: false },
];

type RoleConfig = {
  features: Feature[];
  roleTitle: string;
  accent: string; // tailwind text color
  iconBg: string; // tile bg
  pill: string; // role pill classes
  steps: { label: string }[];
};

function timeGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const { user, clearAuth } = useAuthStore();
  const router = useRouter();

  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");
  const isFaculty = user?.role === "FACULTY";

  let config: RoleConfig;

  if (isAdmin) {
    config = {
      features: ADMIN_FEATURES,
      roleTitle:
        user?.role === "SUPER_ADMIN" || user?.roles?.includes("SUPER_ADMIN")
          ? "Super Admin"
          : "Academic Admin",
      accent: "text-[#ff9900]",
      iconBg: "bg-[#ff9900]/10 text-[#ff9900]",
      pill: "border-[#ff9900]/30 bg-[#ff9900]/10 text-[#b86e00]",
      steps: [
        { label: "Upload a timetable image in the Timetable section" },
        { label: "AI extracts schedules automatically" },
        { label: "Manage student records and announcements" },
      ],
    };
  } else if (isFaculty) {
    config = {
      features: FACULTY_FEATURES,
      roleTitle: "Professor",
      accent: "text-emerald-600",
      iconBg: "bg-emerald-500/10 text-emerald-600",
      pill: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700",
      steps: [
        { label: "Create your classroom and add students" },
        { label: "Assign classwork to your students" },
        { label: "Post announcements and track attendance" },
      ],
    };
  } else {
    config = {
      features: STUDENT_FEATURES,
      roleTitle: "Student",
      accent: "text-blue-600",
      iconBg: "bg-blue-500/10 text-blue-600",
      pill: "border-blue-500/30 bg-blue-500/10 text-blue-700",
      steps: [
        { label: "View your timetable in the Dashboard" },
        { label: "Check attendance records" },
        { label: "Receive notifications for important updates" },
      ],
    };
  }

  const firstName = user?.full_name?.split(" ")[0] ?? "there";
  const initials =
    user?.full_name
      ?.split(" ")
      .slice(0, 2)
      .map((n) => n[0])
      .join("")
      .toUpperCase() ?? "U";

  function handleLogout() {
    clearAuth();
    router.push("/");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top navbar */}
      <header className="sticky top-0 z-20 border-b border-white/5 bg-[#131921] text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/dashboard" className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] text-sm font-black text-[#131921]">
              C
            </span>
            Campus<span className="-ml-1 text-[#ff9900]">OS</span>
          </Link>

          <div className="flex items-center gap-3">
            <NotificationBell />
            <div className="hidden items-center gap-2 sm:flex">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-sm font-semibold">
                {initials}
              </div>
              <div className="leading-tight">
                <div className="text-sm font-medium">{user?.full_name ?? "User"}</div>
                <div className="text-xs text-white/50">{config.roleTitle}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm font-medium text-white/90 transition hover:border-[#ff9900]/50 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
        {/* Welcome header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
                {timeGreeting()}, {firstName} 👋
              </h1>
            </div>
            <p className="mt-1 text-sm text-slate-500">{user?.email}</p>
          </div>
          <span
            className={`inline-flex w-fit items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ${config.pill}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {config.roleTitle}
          </span>
        </div>

        {/* Smart Daily Digest — students */}
        {!isAdmin && !isFaculty && <DailyDigest />}

        {/* Features */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Available Features</h2>
            <span className="text-sm text-slate-400">{config.roleTitle} tools</span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {config.features
              .filter((feature) => feature.active)
              .map((feature) => {
                const Icon = feature.icon;
                return (
                  <Link key={feature.title} href={feature.href}>
                    <div className="group relative flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-[#ff9900] hover:shadow-md">
                      <div className="mb-3 flex items-center justify-between">
                        <span className={`inline-flex h-11 w-11 items-center justify-center rounded-lg ${config.iconBg}`}>
                          <Icon className="h-5 w-5" />
                        </span>
                      </div>
                      <h3 className="font-semibold text-slate-900">{feature.title}</h3>
                      <p className="mt-1 flex-1 text-sm text-slate-500">
                        {feature.description}
                      </p>
                      <div className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[#b86e00] opacity-0 transition group-hover:opacity-100">
                        Open
                        <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                      </div>
                    </div>
                  </Link>
                );
              })}
          </div>
        </section>

        {/* Getting started */}
        <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#ff9900]/10 text-[#ff9900]">
              <Sparkles className="h-4 w-4" />
            </span>
            <h2 className="text-lg font-bold text-slate-900">Getting Started</h2>
          </div>
          <ol className="space-y-3">
            {config.steps.map((step, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="mt-0.5 inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-[#ff9900] text-xs font-bold text-[#131921]">
                  {idx + 1}
                </span>
                <span className="text-sm text-slate-600">{step.label}</span>
              </li>
            ))}
          </ol>
        </section>
      </main>

      {/* Floating AI assistant launcher */}
      <Link
        href="/dashboard/assistant"
        className="fixed bottom-5 right-5 z-40 inline-flex items-center gap-2 rounded-full bg-gradient-to-b from-[#febd69] to-[#ff9900] px-5 py-3 font-semibold text-[#131921] shadow-xl shadow-[#ff9900]/30 transition hover:brightness-105"
      >
        <Bot className="h-5 w-5" />
        <span className="hidden sm:inline">Ask AI</span>
      </Link>
    </div>
  );
}
