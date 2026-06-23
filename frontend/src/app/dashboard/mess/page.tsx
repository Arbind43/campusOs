"use client";

import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import {
  getMess,
  uploadMess,
  confirmMess,
  MessEntry,
  getTodayRatings,
  rateMeal,
  getMessSentiment,
  MessSentiment,
} from "@/lib/mess-api";
import { getErrorMessage } from "@/lib/api";
import {
  Utensils,
  Upload,
  Plus,
  Trash2,
  Save,
  CheckCircle2,
  Clock,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Meh,
  TrendingUp,
  AlertTriangle,
  Smile,
} from "lucide-react";

const DAYS = ["Daily", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const MEALS = ["breakfast", "lunch", "snacks", "dinner"];
const MEAL_EMOJI: Record<string, string> = {
  breakfast: "🌅",
  lunch: "🍛",
  snacks: "☕",
  dinner: "🌙",
};

export default function MessPage() {
  const { user, token } = useAuthStore();
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");

  const [saved, setSaved] = useState<MessEntry[]>([]);
  const [draft, setDraft] = useState<MessEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Convert a saved entry (HH:MM:SS) into an editable draft row (HH:MM).
  function toEditable(e: MessEntry): MessEntry {
    return {
      day_of_week: e.day_of_week || "Daily",
      meal_type: (e.meal_type || "breakfast").toLowerCase(),
      start_time: e.start_time ? e.start_time.slice(0, 5) : "",
      end_time: e.end_time ? e.end_time.slice(0, 5) : "",
      items: e.items || "",
      is_special: !!e.is_special,
    };
  }

  async function refresh(seedDraft = true) {
    setLoading(true);
    try {
      const data = await getMess();
      setSaved(data);
      // Seed the editor with the full saved menu so new rows are ADDED,
      // not replacing the existing menu on save.
      if (seedDraft && isAdmin) setDraft(data.map(toEditable));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setMsg(null);
    try {
      const res = await uploadMess(file);
      if (!res.success) {
        setError(res.message);
      } else {
        // Append parsed rows to the current draft (don't wipe the existing menu).
        setDraft((prev) => [
          ...prev,
          ...res.entries.map((en) => ({
            day_of_week: en.day_of_week || "Daily",
            meal_type: (en.meal_type || "breakfast").toLowerCase(),
            start_time: en.start_time ? en.start_time.slice(0, 5) : "",
            end_time: en.end_time ? en.end_time.slice(0, 5) : "",
            items: en.items || "",
            is_special: !!en.is_special,
          })),
        ]);
        setMsg(res.message);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function addRow() {
    setDraft((prev) => [
      ...prev,
      { day_of_week: "Daily", meal_type: "breakfast", start_time: "", end_time: "", items: "", is_special: false },
    ]);
  }

  function updateRow(i: number, patch: Partial<MessEntry>) {
    setDraft((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }

  function removeRow(i: number) {
    setDraft((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function saveDraft() {
    if (draft.length === 0) return;
    setSavingDraft(true);
    setError(null);
    setMsg(null);
    try {
      const payload = draft.map((d) => ({
        ...d,
        start_time: d.start_time || null,
        end_time: d.end_time || null,
      }));
      const res = await confirmMess(payload);
      setMsg(res.message);
      refresh(); // reloads saved + reseeds the editor with the full menu
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingDraft(false);
    }
  }

  function fmt(t: string | null) {
    if (!t) return "";
    // backend returns HH:MM:SS
    const [h, m] = t.split(":");
    const hour = Number(h);
    const ampm = hour >= 12 ? "PM" : "AM";
    const h12 = hour % 12 || 12;
    return `${h12}:${m} ${ampm}`;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />
      <main className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
            <Utensils className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Mess Menu</h1>
            <p className="text-sm text-slate-500">
              {isAdmin ? "Upload a menu photo or edit meals manually" : "This week's meals & timings"}
            </p>
          </div>
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
        )}
        {msg && (
          <p className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4" /> {msg}
          </p>
        )}

        {/* Warden sentiment dashboard (admins) */}
        {isAdmin && <SentimentDashboard />}

        {/* 1-tap meal rating (students) */}
        {!isAdmin && <MealRatings />}

        {/* Admin upload + editor */}
        {isAdmin && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Upload className="h-5 w-5 text-[#ff9900]" />
                <h2 className="font-semibold text-slate-900">Upload Menu</h2>
              </div>
              <div className="flex gap-2">
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleFile}
                  className="hidden"
                />
                <button
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-[#ff9900] hover:text-[#b86e00] disabled:opacity-60"
                >
                  {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  {uploading ? "Parsing…" : "Upload Image"}
                </button>
                <button
                  onClick={addRow}
                  className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  <Plus className="h-4 w-4" /> Add meal
                </button>
              </div>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              Upload a photo of the weekly mess menu — AI extracts the meals for you to review,
              or add rows manually. Saving replaces the current schedule.
            </p>

            {draft.length > 0 && (
              <div className="mt-5 space-y-3">
                {draft.map((row, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-1 gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 sm:grid-cols-12 sm:items-center"
                  >
                    <select
                      value={row.day_of_week}
                      onChange={(e) => updateRow(i, { day_of_week: e.target.value })}
                      className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm sm:col-span-2"
                    >
                      {DAYS.map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                    <select
                      value={row.meal_type}
                      onChange={(e) => updateRow(i, { meal_type: e.target.value })}
                      className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm capitalize sm:col-span-2"
                    >
                      {MEALS.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <input
                      type="time"
                      value={row.start_time ?? ""}
                      onChange={(e) => updateRow(i, { start_time: e.target.value })}
                      className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm sm:col-span-1"
                    />
                    <input
                      type="time"
                      value={row.end_time ?? ""}
                      onChange={(e) => updateRow(i, { end_time: e.target.value })}
                      className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm sm:col-span-1"
                    />
                    <input
                      value={row.items}
                      onChange={(e) => updateRow(i, { items: e.target.value })}
                      placeholder="Dishes, comma separated"
                      className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm sm:col-span-5"
                    />
                    <button
                      onClick={() => removeRow(i)}
                      className="inline-flex items-center justify-center rounded-md p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-600 sm:col-span-1"
                      aria-label="Remove"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={saveDraft}
                  disabled={savingDraft}
                  className="inline-flex items-center gap-2 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] px-5 py-2.5 text-sm font-semibold text-[#131921] shadow-sm transition hover:brightness-105 disabled:opacity-60"
                >
                  <Save className="h-4 w-4" />
                  {savingDraft ? "Saving…" : `Save ${draft.length} meal(s)`}
                </button>
              </div>
            )}
          </section>
        )}

        {/* Saved schedule */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Current Menu</h2>
          {loading ? (
            <p className="text-sm text-slate-400">Loading…</p>
          ) : saved.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
              No mess menu uploaded yet.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {saved.map((m) => (
                <div
                  key={m.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{MEAL_EMOJI[m.meal_type] ?? "🍽️"}</span>
                      <div>
                        <h3 className="font-semibold capitalize text-slate-900">
                          {m.meal_type}
                        </h3>
                        <span className="text-xs text-slate-400">{m.day_of_week}</span>
                      </div>
                    </div>
                    {(m.start_time || m.end_time) && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-[#ff9900]/10 px-2.5 py-1 text-xs font-medium text-[#b86e00]">
                        <Clock className="h-3 w-3" />
                        {fmt(m.start_time)}{m.end_time ? ` – ${fmt(m.end_time)}` : ""}
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{m.items}</p>
                  {m.is_special && (
                    <span className="mt-2 inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
                      ✨ Special
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}


/* ── 1-tap meal rating (students) ─────────────────────────────────────────── */

const RATE_MEALS = ["breakfast", "lunch", "snacks", "dinner"];
const RATE_EMOJI: Record<string, string> = {
  breakfast: "🌅",
  lunch: "🍛",
  snacks: "☕",
  dinner: "🌙",
};
const TAPS = [
  { value: 5, Icon: ThumbsUp, label: "Good", active: "bg-emerald-500 text-white border-emerald-500" },
  { value: 3, Icon: Meh, label: "Okay", active: "bg-amber-500 text-white border-amber-500" },
  { value: 1, Icon: ThumbsDown, label: "Poor", active: "bg-red-500 text-white border-red-500" },
];

function MealRatings() {
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    getTodayRatings().then((r) => setRatings(r.ratings)).catch(() => {});
  }, []);

  async function tap(meal: string, value: number) {
    setSaving(meal);
    // optimistic
    setRatings((p) => ({ ...p, [meal]: value }));
    try {
      const res = await rateMeal(meal, value);
      setRatings(res.ratings);
    } catch {
      /* ignore */
    } finally {
      setSaving(null);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <Smile className="h-5 w-5 text-[#ff9900]" />
        <h2 className="font-semibold text-slate-900">Rate today&apos;s meals</h2>
      </div>
      <p className="mb-4 text-sm text-slate-500">One tap — anonymous. Helps the warden improve the menu.</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {RATE_MEALS.map((meal) => (
          <div key={meal} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
            <span className="flex items-center gap-2 text-sm font-medium capitalize text-slate-800">
              <span className="text-lg">{RATE_EMOJI[meal]}</span> {meal}
            </span>
            <div className="flex gap-1.5">
              {TAPS.map(({ value, Icon, label, active }) => {
                const on = ratings[meal] === value;
                return (
                  <button
                    key={value}
                    onClick={() => tap(meal, value)}
                    disabled={saving === meal}
                    title={label}
                    className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border transition ${
                      on ? active : "border-slate-200 bg-white text-slate-400 hover:border-slate-300"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── Warden sentiment dashboard ───────────────────────────────────────────── */

function avgColor(avg: number) {
  if (!avg) return "text-slate-400";
  if (avg >= 3.5) return "text-emerald-600";
  if (avg >= 2.5) return "text-amber-600";
  return "text-red-600";
}

function SentimentDashboard() {
  const [data, setData] = useState<MessSentiment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const load = () =>
      getMessSentiment()
        .then((d) => active && setData(d))
        .catch(() => {})
        .finally(() => active && setLoading(false));
    load();
    const id = setInterval(load, 20000); // real-time-ish polling
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  if (loading) return <p className="text-sm text-slate-400">Loading sentiment…</p>;
  if (!data) return null;

  const maxAvg = 5;

  return (
    <section className="space-y-4">
      {/* Nudges */}
      {data.alerts.length > 0 && (
        <div className="space-y-2">
          {data.alerts.map((a, i) => (
            <div key={i} className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{a}</span>
            </div>
          ))}
        </div>
      )}

      {/* Today overview */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Today&apos;s meal sentiment</h2>
          <span className="flex items-center gap-1 text-xs text-slate-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" /> live · {data.total} ratings
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {data.meals.map((m) => (
            <div key={m.meal_type} className="rounded-xl border border-slate-100 p-4 text-center">
              <span className="text-2xl">{MEAL_EMOJI[m.meal_type] ?? "🍽️"}</span>
              <p className="mt-1 text-xs font-medium capitalize text-slate-500">{m.meal_type}</p>
              <p className={`mt-1 text-2xl font-bold ${avgColor(m.avg)}`}>
                {m.avg || "–"}
                {m.avg ? <span className="text-sm text-slate-400">/5</span> : null}
              </p>
              <p className="text-[11px] text-slate-400">{m.count} ratings</p>
              {m.count > 0 && (
                <div className="mt-2 flex h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div className="bg-emerald-500" style={{ width: `${m.positive_pct}%` }} />
                  <div className="bg-red-400" style={{ width: `${m.negative_pct}%` }} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 7-day trend */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-900">
          <TrendingUp className="h-4 w-4 text-[#ff9900]" /> 7-day satisfaction trend
        </h2>
        <div className="flex items-end justify-between gap-2" style={{ height: 130 }}>
          {data.trend.map((t) => (
            <div key={t.day} className="flex flex-1 flex-col items-center justify-end gap-1">
              <span className="text-[10px] font-medium text-slate-500">{t.avg || ""}</span>
              <div
                className={`w-full rounded-t-md ${
                  t.avg >= 3.5 ? "bg-emerald-500" : t.avg >= 2.5 ? "bg-amber-400" : t.avg ? "bg-red-400" : "bg-slate-200"
                }`}
                style={{ height: `${((t.avg || 0) / maxAvg) * 100}%`, minHeight: 4 }}
              />
              <span className="text-[10px] text-slate-400">
                {new Date(t.day).toLocaleDateString(undefined, { weekday: "short" })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
