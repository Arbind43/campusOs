"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  CalendarDays,
  FileText,
  CalendarClock,
  Bell,
  AlertTriangle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { getDigest, DigestResponse } from "@/lib/digest-api";

export default function DailyDigest() {
  const [data, setData] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    getDigest()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-400">Preparing your daily digest…</p>
      </div>
    );
  }
  if (!data) return null;

  const hasItems =
    data.classes.length ||
    data.assignments.length ||
    data.deadlines.length ||
    data.attendance_alerts.length ||
    data.notices.length ||
    data.events.length;

  return (
    <div className="overflow-hidden rounded-2xl border border-[#ff9900]/30 bg-gradient-to-br from-[#131921] to-[#1b2733] text-white shadow-lg">
      {/* Insight header */}
      <div className="flex items-start gap-3 p-5 sm:p-6">
        <span className="mt-0.5 inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-b from-[#febd69] to-[#ff9900] text-[#131921]">
          <Sparkles className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-[#febd69]">
              Smart Daily Digest · {data.date}
            </span>
            <button
              onClick={() => setOpen((v) => !v)}
              className="text-white/50 transition hover:text-white"
              aria-label={open ? "Collapse" : "Expand"}
            >
              {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
          <p className="mt-1 text-base font-medium leading-snug text-white sm:text-lg">
            {data.insight}
          </p>

          {/* Quick-action pills */}
          {data.quick_actions.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {data.quick_actions.map((q) => (
                <Link
                  key={q}
                  href={`/dashboard/assistant?q=${encodeURIComponent(q)}`}
                  className="inline-flex items-center gap-1 rounded-full border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/90 backdrop-blur transition hover:border-[#ff9900]/60 hover:bg-white/10"
                >
                  {q}
                  <ArrowRight className="h-3 w-3" />
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Expandable detail cards */}
      {open && hasItems && (
        <div className="grid gap-px bg-white/10 sm:grid-cols-2 lg:grid-cols-3">
          {/* Today's classes */}
          {data.classes.length > 0 && (
            <DigestCard icon={CalendarDays} title="Today's classes" tint="bg-[#0d141d]">
              {data.classes.map((c, i) => (
                <li key={i} className="flex items-center justify-between gap-2">
                  <span className={c.at_risk ? "font-medium text-amber-300" : ""}>
                    {c.subject}
                    {c.at_risk && " ⚠️"}
                  </span>
                  <span className="text-white/50">
                    {c.start} · {c.room || "—"}
                  </span>
                </li>
              ))}
            </DigestCard>
          )}

          {/* Attendance alerts */}
          {data.attendance_alerts.length > 0 && (
            <DigestCard icon={AlertTriangle} title="Attendance watch" tint="bg-[#0d141d]">
              {data.attendance_alerts.map((a, i) => (
                <li key={i}>
                  <span className={a.urgent ? "font-medium text-red-300" : ""}>{a.title}</span>
                  <span className="block text-white/50">{a.subtitle}{a.when ? ` · ${a.when}` : ""}</span>
                </li>
              ))}
            </DigestCard>
          )}

          {/* Assignments */}
          {data.assignments.length > 0 && (
            <DigestCard icon={FileText} title="Assignments" tint="bg-[#0d141d]">
              {data.assignments.map((a, i) => (
                <li key={i} className="flex items-center justify-between gap-2">
                  <span className={a.urgent ? "font-medium text-amber-300" : ""}>{a.title}</span>
                  <span className="text-white/50">{a.when}</span>
                </li>
              ))}
            </DigestCard>
          )}

          {/* Deadlines */}
          {data.deadlines.length > 0 && (
            <DigestCard icon={CalendarClock} title="Deadlines" tint="bg-[#0d141d]">
              {data.deadlines.map((d, i) => (
                <li key={i} className="flex items-center justify-between gap-2">
                  <span className={d.urgent ? "font-medium text-amber-300" : ""}>{d.title}</span>
                  <span className="text-white/50">{d.when}</span>
                </li>
              ))}
            </DigestCard>
          )}

          {/* Notices */}
          {data.notices.length > 0 && (
            <DigestCard icon={Bell} title="Notices" tint="bg-[#0d141d]">
              {data.notices.map((n, i) => (
                <li key={i}>
                  <span className={n.urgent ? "font-medium text-[#febd69]" : ""}>
                    {n.urgent ? "📌 " : ""}{n.title}
                  </span>
                </li>
              ))}
            </DigestCard>
          )}

          {/* Events */}
          {data.events.length > 0 && (
            <DigestCard icon={CalendarDays} title="Events" tint="bg-[#0d141d]">
              {data.events.map((e, i) => (
                <li key={i} className="flex items-center justify-between gap-2">
                  <span>{e.title}</span>
                  <span className="text-white/50">{e.when}</span>
                </li>
              ))}
            </DigestCard>
          )}
        </div>
      )}
    </div>
  );
}

function DigestCard({
  icon: Icon,
  title,
  tint,
  children,
}: {
  icon: typeof CalendarDays;
  title: string;
  tint: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`${tint} p-4`}>
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[#ff9900]">
        <Icon className="h-3.5 w-3.5" />
        {title}
      </div>
      <ul className="space-y-1.5 text-sm text-white/85">{children}</ul>
    </div>
  );
}
