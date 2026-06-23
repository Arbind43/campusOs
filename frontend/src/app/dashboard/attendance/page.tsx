"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { listDepartments, Department } from "@/lib/notices-api";
import {
  listStudents,
  markAttendance,
  getMyAttendance,
  getAttendancePrediction,
  StudentBrief,
  AttendanceSummary,
  AttendancePrediction,
  AttendanceStatus,
} from "@/lib/attendance-api";
import { getErrorMessage } from "@/lib/api";
import {
  BarChart3,
  CheckCircle2,
  Users,
  Save,
  CalendarDays,
  AlertTriangle,
  TrendingDown,
  ShieldCheck,
} from "lucide-react";

const STATUS_OPTIONS: { value: AttendanceStatus; label: string; classes: string }[] = [
  { value: "present", label: "Present", classes: "bg-emerald-500 text-white border-emerald-500" },
  { value: "absent", label: "Absent", classes: "bg-red-500 text-white border-red-500" },
  { value: "late", label: "Late", classes: "bg-amber-500 text-white border-amber-500" },
];

export default function AttendancePage() {
  const { user, token } = useAuthStore();
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.role === "FACULTY" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN") ||
    user?.roles?.includes("FACULTY");

  if (!token) {
    return (
      <div className="min-h-screen bg-slate-50">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
          <p className="text-slate-400">Loading…</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />
      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
            <BarChart3 className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Attendance</h1>
            <p className="text-sm text-slate-500">
              {isAdmin ? "Mark and manage student attendance" : "Your attendance record"}
            </p>
          </div>
        </div>

        {isAdmin ? <AdminAttendance /> : <StudentAttendance />}
      </main>
    </div>
  );
}

function AdminAttendance() {
  const today = new Date().toISOString().slice(0, 10);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [deptId, setDeptId] = useState("");
  const [year, setYear] = useState("");
  const [subject, setSubject] = useState("General");
  const [date, setDate] = useState(today);

  const [students, setStudents] = useState<StudentBrief[]>([]);
  const [statuses, setStatuses] = useState<Record<string, AttendanceStatus>>({});
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    listDepartments()
      .then((d) => {
        setDepartments(d);
        if (d.length) setDeptId(d[0].id);
      })
      .catch(() => setDepartments([]));
  }, []);

  async function loadRoster() {
    if (!deptId) {
      setError("Select a department first.");
      return;
    }
    setError(null);
    setSuccess(null);
    setLoadingRoster(true);
    try {
      const list = await listStudents(deptId, year ? Number(year) : undefined);
      setStudents(list);
      // default everyone to present
      const init: Record<string, AttendanceStatus> = {};
      list.forEach((s) => (init[s.id] = "present"));
      setStatuses(init);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoadingRoster(false);
    }
  }

  async function save() {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await markAttendance({
        department_id: deptId,
        year_of_study: year ? Number(year) : null,
        subject,
        attend_date: date,
        records: students.map((s) => ({ student_id: s.id, status: statuses[s.id] })),
      });
      setSuccess(res.message);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  const presentCount = useMemo(
    () => Object.values(statuses).filter((s) => s === "present").length,
    [statuses]
  );

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">Department</label>
            <select
              value={deptId}
              onChange={(e) => setDeptId(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
            >
              <option value="">Select…</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">Year</label>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
            >
              <option value="">All Years</option>
              {[1, 2, 3, 4].map((y) => (
                <option key={y} value={y}>
                  Year {y}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">Subject</label>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
            />
          </div>
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
              <CalendarDays className="h-3.5 w-3.5" /> Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
            />
          </div>
        </div>
        <button
          onClick={loadRoster}
          disabled={loadingRoster}
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
        >
          <Users className="h-4 w-4" />
          {loadingRoster ? "Loading…" : "Load Students"}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </p>
      )}
      {success && (
        <p className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4" /> {success}
        </p>
      )}

      {/* Roster */}
      {students.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">
              {students.length} student{students.length !== 1 && "s"}
            </h2>
            <span className="text-sm text-slate-500">
              {presentCount}/{students.length} present
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {students.map((s) => (
              <div
                key={s.id}
                className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                    {s.full_name.split(" ").slice(0, 2).map((n) => n[0]).join("").toUpperCase()}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{s.full_name}</p>
                    <p className="text-xs text-slate-400">
                      {s.email}
                      {s.year_of_study ? ` · Year ${s.year_of_study}` : ""}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1.5">
                  {STATUS_OPTIONS.map((opt) => {
                    const active = statuses[s.id] === opt.value;
                    return (
                      <button
                        key={opt.value}
                        onClick={() =>
                          setStatuses((prev) => ({ ...prev, [s.id]: opt.value }))
                        }
                        className={`rounded-md border px-3 py-1.5 text-xs font-semibold transition ${
                          active
                            ? opt.classes
                            : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
                        }`}
                      >
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={save}
            disabled={saving}
            className="mt-5 inline-flex items-center gap-2 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] px-5 py-2.5 text-sm font-semibold text-[#131921] shadow-sm transition hover:brightness-105 disabled:opacity-60"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving…" : "Save Attendance"}
          </button>
        </div>
      )}

      {students.length === 0 && !loadingRoster && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
          Select filters and load students to begin marking attendance.
        </div>
      )}
    </div>
  );
}

function StudentAttendance() {
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [prediction, setPrediction] = useState<AttendancePrediction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMyAttendance(), getAttendancePrediction()])
      .then(([s, p]) => {
        setSummary(s);
        setPrediction(p);
      })
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-400">Loading…</p>;
  if (!summary || summary.total === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
        No attendance has been recorded for you yet.
      </div>
    );
  }

  const pct = summary.percentage;
  const ring =
    pct >= 75 ? "text-emerald-500" : pct >= 60 ? "text-amber-500" : "text-red-500";

  const STATUS_STYLES: Record<string, { badge: string; bar: string; label: string }> = {
    safe: { badge: "bg-emerald-50 text-emerald-700", bar: "bg-emerald-500", label: "Safe" },
    warning: { badge: "bg-amber-50 text-amber-700", bar: "bg-amber-500", label: "At risk" },
    critical: { badge: "bg-red-50 text-red-700", bar: "bg-red-500", label: "Critical" },
  };

  return (
    <div className="space-y-6">
      {/* Predictor banner */}
      {prediction && (
        <div
          className={`flex items-start gap-3 rounded-2xl border p-4 ${
            prediction.overall_status === "critical"
              ? "border-red-200 bg-red-50"
              : prediction.overall_status === "warning"
              ? "border-amber-200 bg-amber-50"
              : "border-emerald-200 bg-emerald-50"
          }`}
        >
          <span
            className={`mt-0.5 inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${
              prediction.overall_status === "critical"
                ? "bg-red-500/15 text-red-600"
                : prediction.overall_status === "warning"
                ? "bg-amber-500/15 text-amber-600"
                : "bg-emerald-500/15 text-emerald-600"
            }`}
          >
            {prediction.overall_status === "critical" ? (
              <AlertTriangle className="h-5 w-5" />
            ) : prediction.overall_status === "warning" ? (
              <TrendingDown className="h-5 w-5" />
            ) : (
              <ShieldCheck className="h-5 w-5" />
            )}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-900">Attendance Predictor</h3>
              <span className="rounded-full bg-white/70 px-2 py-0.5 text-[11px] font-semibold text-slate-500">
                min {prediction.threshold}%
              </span>
            </div>
            <p className="mt-0.5 text-sm text-slate-700">{prediction.summary}</p>
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-4">
        <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:col-span-1">
          <span className={`text-4xl font-bold ${ring}`}>{pct}%</span>
          <span className="mt-1 text-sm text-slate-500">Overall</span>
        </div>
        <div className="grid grid-cols-3 gap-4 sm:col-span-3">
          {[
            { label: "Present", value: summary.present, color: "text-emerald-600" },
            { label: "Late", value: summary.late, color: "text-amber-600" },
            { label: "Absent", value: summary.absent, color: "text-red-600" },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm"
            >
              <span className={`text-3xl font-bold ${s.color}`}>{s.value}</span>
              <p className="mt-1 text-sm text-slate-500">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Per-subject prediction */}
      {prediction && prediction.subjects.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 font-semibold text-slate-900">By Subject</h2>
          <div className="space-y-3">
            {prediction.subjects.map((s) => {
              const st = STATUS_STYLES[s.status];
              return (
                <div key={s.subject} className="rounded-xl border border-slate-100 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{s.subject}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${st.badge}`}>
                        {st.label}
                      </span>
                    </div>
                    <span className="text-sm font-bold text-slate-900">{s.percentage}%</span>
                  </div>
                  {/* progress bar */}
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full ${st.bar}`}
                      style={{ width: `${Math.min(s.percentage, 100)}%` }}
                    />
                  </div>
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm text-slate-600">{s.message}</p>
                    <span className="text-xs text-slate-400">
                      {s.present}/{s.total} attended
                      {s.status === "critical"
                        ? ` · attend ${s.must_attend} to recover`
                        : ` · can miss ${s.can_miss}`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-semibold text-slate-900">Recent Records</h2>
        <div className="divide-y divide-slate-100">
          {summary.records.slice(0, 20).map((r) => (
            <div key={r.id} className="flex items-center justify-between py-2.5 text-sm">
              <div>
                <span className="font-medium text-slate-800">{r.subject}</span>
                <span className="ml-2 text-slate-400">{r.attend_date}</span>
              </div>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                  r.status === "present"
                    ? "bg-emerald-50 text-emerald-700"
                    : r.status === "late"
                    ? "bg-amber-50 text-amber-700"
                    : "bg-red-50 text-red-700"
                }`}
              >
                {r.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
