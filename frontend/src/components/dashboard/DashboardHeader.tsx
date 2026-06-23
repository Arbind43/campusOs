"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/auth";

/**
 * Shared dark navbar for dashboard sub-pages, with an optional back link.
 */
export default function DashboardHeader({
  backHref = "/dashboard",
  backLabel = "Dashboard",
}: {
  backHref?: string;
  backLabel?: string;
}) {
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();

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
    <header className="sticky top-0 z-20 border-b border-white/5 bg-[#131921] text-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-4">
          <Link
            href={backHref}
            className="inline-flex items-center gap-1.5 rounded-md border border-white/15 bg-white/5 px-3 py-1.5 text-sm font-medium text-white/80 transition hover:border-[#ff9900]/50 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">{backLabel}</span>
          </Link>
          <Link href="/dashboard" className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] text-sm font-black text-[#131921]">
              C
            </span>
            Campus<span className="-ml-1 text-[#ff9900]">OS</span>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden h-9 w-9 items-center justify-center rounded-full bg-white/10 text-sm font-semibold sm:flex">
            {initials}
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
  );
}
