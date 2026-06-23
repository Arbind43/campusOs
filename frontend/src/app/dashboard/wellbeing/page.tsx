"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import {
  getCheckinStatus,
  submitCheckin,
  getInsights,
  WellbeingInsights,
} from "@/lib/wellbeing-api";
import { getErrorMessage } from "@/lib/api";
import {
  HeartPulse,
  Lock,
  CheckCircle2,
  TrendingUp,
  Users,
  ShieldCheck,
  AlertTriangle,
  Activity,
} from "lucide-react";

export default function WellbeingPage() {
  const { user, token } = useAuthStore();
  const isCounsellor =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN") ||
    user?.roles?.includes("COUNSELLOR");

  if (!token) {
    return (
      <div className="min-h-screen bg-slate-50">
        <DashboardHeader />
        <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
          <p className="text-slate-400">Loading…</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />
      <main className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
            <HeartPulse className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Wellbeing</h1>
            <p className="text-sm text-slate-500">
              {isCounsellor
                ? "Anonymous wellbeing insights for your campus"
                : "A quick, anonymous weekly check-in"}
            </p>
          </div>
        </div>

        {isCounsellor ? <Insights /> : <CheckinForm />}
      </main>
    </div>
  );
}

/* ── Student check-in ─────────────────────────────────────────────────────── */

const QUESTIONS = [
  {
    key: "mood" as const,
    label: "How has your mood been this week?",
    options: ["😣", "🙁", "😐", "🙂", "😄"],
    captions: ["Very low", "Low", "Okay", "Good", "Great"],
  },
  {
    key: "stress" as const,
    label: "How stressed have you felt?",
    options: ["😌", "🙂", "😐", "😟", "😰"],
    captions: ["None", "A little", "Moderate", "High", "Overwhelmed"],
  },
  {
    key: "sleep" as const,
    label: "How well have you been sleeping?",
    options: ["😴", "😪", "😐", "🙂", "😄"],
    captions: ["Poor", "Restless", "Okay", "Good", "Excellent"],
  },
];

function CheckinForm() {
  const [status, setStatus] = useState<{ submitted: boolean; week_start: string } | null>(null);
  const [answers, setAnswers] = useState<{ mood?: number; stress?: number; sleep?: number }>({});
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    getCheckinStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  const allAnswered = answers.mood && answers.stress && answers.sleep;

  async function handleSubmit() {
    if (!allAnswered) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitCheckin({
        mood: answers.mood!,
        stress: answers.stress!,
        sleep: answers.sleep!,
        note: note || null,
      });
      setDone(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (done || status?.submitted) {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-10 text-center">
        <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
        <h2 className="mt-3 text-lg font-bold text-slate-900">Thanks for checking in 💚</h2>
        <p className="mt-1 text-sm text-slate-600">
          Your response is completely anonymous. See you next week!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
        <Lock className="h-4 w-4 text-emerald-600" />
        Your answers are <span className="font-semibold">anonymous</span> — we never store who submitted.
      </div>

      {QUESTIONS.map((q) => (
        <div key={q.key} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">{q.label}</h3>
          <div className="grid grid-cols-5 gap-2">
            {q.options.map((emoji, i) => {
              const value = i + 1;
              const active = answers[q.key] === value;
              return (
                <button
                  key={value}
                  onClick={() => setAnswers((p) => ({ ...p, [q.key]: value }))}
                  className={`flex flex-col items-center gap-1 rounded-xl border p-3 transition ${
                    active
                      ? "border-[#ff9900] bg-[#ff9900]/10"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <span className="text-2xl">{emoji}</span>
                  <span className={`text-[11px] ${active ? "font-semibold text-[#b86e00]" : "text-slate-500"}`}>
                    {q.captions[i]}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-2 font-semibold text-slate-900">
          Anything on your mind? <span className="text-xs font-normal text-slate-400">(optional, anonymous)</span>
        </h3>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={3}
          maxLength={500}
          placeholder="Share anything you'd like the wellbeing team to know…"
          className="w-full resize-none rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
        />
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      <button
        onClick={handleSubmit}
        disabled={!allAnswered || submitting}
        className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] py-3 text-sm font-semibold text-[#131921] shadow-sm transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? "Submitting…" : "Submit anonymously"}
      </button>
    </div>
  );
}

/* ── Counsellor insights ──────────────────────────────────────────────────── */

const STATUS_MAP = {
  calm: { label: "Calm", cls: "border-emerald-200 bg-emerald-50", icon: ShieldCheck, color: "text-emerald-600" },
  watch: { label: "Watch", cls: "border-amber-200 bg-amber-50", icon: Activity, color: "text-amber-600" },
  elevated: { label: "Elevated", cls: "border-red-200 bg-red-50", icon: AlertTriangle, color: "text-red-600" },
};

function Insights() {
  const [data, setData] = useState<WellbeingInsights | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInsights()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-400">Loading insights…</p>;
  if (!data) return <p className="text-slate-400">Could not load insights.</p>;

  const st = STATUS_MAP[data.status];
  const StatusIcon = st.icon;
  const maxStress = Math.max(...data.trend.map((t) => t.avg_stress), 5);

  return (
    <div className="space-y-6">
      {/* AI insight banner */}
      <div className={`flex items-start gap-3 rounded-2xl border p-5 ${st.cls}`}>
        <span className={`mt-0.5 inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-white/70 ${st.color}`}>
          <StatusIcon className="h-5 w-5" />
        </span>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-slate-900">AI Insight</h2>
            <span className={`rounded-full bg-white/70 px-2 py-0.5 text-[11px] font-semibold ${st.color}`}>
              {st.label}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-700">{data.insight}</p>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Responses", value: data.responses, suffix: "" },
          { label: "Avg mood", value: data.avg_mood, suffix: "/5" },
          { label: "Avg stress", value: data.avg_stress, suffix: "/5" },
          { label: "High stress", value: data.high_stress_pct, suffix: "%" },
        ].map((m) => (
          <div key={m.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <span className="text-2xl font-bold text-slate-900">
              {m.value}
              <span className="text-base text-slate-400">{m.suffix}</span>
            </span>
            <p className="mt-1 text-sm text-slate-500">{m.label}</p>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-3 font-semibold text-slate-900">Recommended actions</h2>
          <ul className="space-y-2">
            {data.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[#ff9900]" />
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* 4-week stress trend */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
            <TrendingUp className="h-4 w-4 text-[#ff9900]" /> Stress trend (4 weeks)
          </h2>
          <div className="flex items-end justify-between gap-3" style={{ height: 140 }}>
            {data.trend.map((t) => (
              <div key={t.week_start} className="flex flex-1 flex-col items-center justify-end gap-2">
                <span className="text-xs font-medium text-slate-500">{t.avg_stress || 0}</span>
                <div
                  className="w-full rounded-t-md bg-gradient-to-t from-[#ff9900] to-[#febd69]"
                  style={{ height: `${((t.avg_stress || 0) / maxStress) * 100}%`, minHeight: 4 }}
                />
                <span className="text-[10px] text-slate-400">
                  {new Date(t.week_start).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Department hotspots */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
            <Users className="h-4 w-4 text-[#ff9900]" /> Department hotspots
          </h2>
          {data.departments.length === 0 ? (
            <p className="text-sm text-slate-400">
              Not enough responses to show cohort breakdowns (min {data.min_cohort} per group, for privacy).
            </p>
          ) : (
            <div className="space-y-3">
              {data.departments.map((d) => (
                <div key={d.department}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-800">{d.department}</span>
                    <span className="text-slate-500">{d.high_stress_pct}% high stress · {d.responses} resp.</span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full ${d.high_stress_pct >= 50 ? "bg-red-500" : d.high_stress_pct >= 30 ? "bg-amber-500" : "bg-emerald-500"}`}
                      style={{ width: `${Math.min(d.high_stress_pct, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <p className="text-center text-xs text-slate-400">
        All data is aggregated and anonymous. Individual responses are never stored with identities.
      </p>
    </div>
  );
}
