"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { listDepartments, Department } from "@/lib/notices-api";
import { checkSlot, scheduleClass, getFreeSlots, SlotCheckResult, FreeSlotsResult } from "@/lib/conflicts-api";
import { getErrorMessage } from "@/lib/api";
import {
  CalendarClock,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Search,
  CalendarPlus,
  ShieldAlert,
  DoorClosed,
  UserCog,
  Users,
  DoorOpen,
  Clock,
} from "lucide-react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const KIND_ICON = { room: DoorClosed, faculty: UserCog, cohort: Users };

export default function ConflictsPage() {
  const { user, token } = useAuthStore();
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");

  const [departments, setDepartments] = useState<Department[]>([]);
  const [deptId, setDeptId] = useState("");
  const [semester, setSemester] = useState("1");
  const [day, setDay] = useState("Monday");
  const [start, setStart] = useState("09:00");
  const [end, setEnd] = useState("10:00");
  const [subject, setSubject] = useState("");
  const [room, setRoom] = useState("");
  const [faculty, setFaculty] = useState("");

  const [checking, setChecking] = useState(false);
  const [scheduling, setScheduling] = useState(false);
  const [result, setResult] = useState<SlotCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [freeSlots, setFreeSlots] = useState<FreeSlotsResult | null>(null);
  const [loadingFree, setLoadingFree] = useState(false);

  async function loadFreeSlots(forDay: string) {
    setLoadingFree(true);
    try {
      setFreeSlots(await getFreeSlots(forDay));
    } catch {
      setFreeSlots(null);
    } finally {
      setLoadingFree(false);
    }
  }

  function fmtTime(t: string) {
    const [h, m] = t.split(":");
    const hr = Number(h);
    const ampm = hr >= 12 ? "PM" : "AM";
    return `${hr % 12 || 12}:${m} ${ampm}`;
  }

  function pickSlot(roomName: string, winStart: string, winEnd: string) {
    // Fill the form with a 1-hour slot starting at the window start (capped to window end).
    setRoom(roomName);
    setStart(winStart.slice(0, 5));
    // default 1h, but not beyond window end
    const [h, m] = winStart.split(":").map(Number);
    const endH = Math.min(h + 1, Number(winEnd.slice(0, 2)));
    const proposedEnd = `${String(endH).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
    setEnd(proposedEnd <= winEnd.slice(0, 5) ? proposedEnd : winEnd.slice(0, 5));
    setResult(null);
    setSuccess(null);
  }

  useEffect(() => {
    if (token && isAdmin) {
      listDepartments()
        .then((d) => {
          setDepartments(d);
          if (d.length) setDeptId(d[0].id);
        })
        .catch(() => setDepartments([]));
      loadFreeSlots(day);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // Any edit invalidates a previous check.
  function invalidate() {
    setResult(null);
    setSuccess(null);
  }

  const slot = () => ({
    department_id: deptId,
    semester: Number(semester),
    day_of_week: day,
    start_time: start,
    end_time: end,
    subject,
    room: room || null,
    faculty_name: faculty || null,
  });

  function validBasics(): string | null {
    if (!deptId) return "Select a department.";
    if (!subject.trim()) return "Enter a subject.";
    if (start >= end) return "End time must be after start time.";
    return null;
  }

  async function handleCheck() {
    const v = validBasics();
    if (v) {
      setError(v);
      return;
    }
    setError(null);
    setSuccess(null);
    setChecking(true);
    try {
      setResult(await checkSlot(slot()));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setChecking(false);
    }
  }

  async function handleSchedule() {
    const v = validBasics();
    if (v) {
      setError(v);
      return;
    }
    setError(null);
    setScheduling(true);
    try {
      await scheduleClass(slot());
      setSuccess(`${subject} scheduled on ${day} (${start}–${end}).`);
      setResult(null);
      setSubject("");
      loadFreeSlots(day);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setScheduling(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-50">
        <DashboardHeader />
        <main className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white p-10 text-center">
            <ShieldAlert className="h-10 w-10 text-slate-400" />
            <h1 className="text-lg font-bold text-slate-900">Admins only</h1>
            <p className="text-sm text-slate-500">This scheduling tool is for administrators.</p>
          </div>
        </main>
      </div>
    );
  }

  const inputCls =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30";

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
            <CalendarClock className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Conflict-free Scheduling</h1>
            <p className="text-sm text-slate-500">
              Check for clashes, then schedule the class
            </p>
          </div>
        </div>

        <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Department</label>
              <select value={deptId} onChange={(e) => { setDeptId(e.target.value); invalidate(); }} className={inputCls}>
                <option value="">Select…</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Semester (year)</label>
              <select value={semester} onChange={(e) => { setSemester(e.target.value); invalidate(); }} className={inputCls}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>Semester {s}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Day</label>
              <select value={day} onChange={(e) => { setDay(e.target.value); invalidate(); loadFreeSlots(e.target.value); }} className={inputCls}>
                {DAYS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Start</label>
              <input type="time" value={start} onChange={(e) => { setStart(e.target.value); invalidate(); }} className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">End</label>
              <input type="time" value={end} onChange={(e) => { setEnd(e.target.value); invalidate(); }} className={inputCls} />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Subject</label>
              <input value={subject} onChange={(e) => { setSubject(e.target.value); invalidate(); }} placeholder="e.g. Bengali" className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Room <span className="text-slate-400">(optional)</span></label>
              <input value={room} onChange={(e) => { setRoom(e.target.value); invalidate(); }} placeholder="A101" className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700">Faculty <span className="text-slate-400">(optional)</span></label>
              <input value={faculty} onChange={(e) => { setFaculty(e.target.value); invalidate(); }} placeholder="Dr. Sharma" className={inputCls} />
            </div>
          </div>

          <button
            onClick={handleCheck}
            disabled={checking}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-slate-900 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
          >
            <Search className="h-4 w-4" />
            {checking ? "Checking…" : "Check for conflicts"}
          </button>
        </div>

        {/* Free rooms & slots for the chosen day */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-1 flex items-center gap-2">
            <DoorOpen className="h-5 w-5 text-emerald-600" />
            <h2 className="font-semibold text-slate-900">Free rooms on {day}</h2>
          </div>
          <p className="mb-4 text-sm text-slate-500">
            Tap a free window to fill the form (working hours 8:00 AM – 6:00 PM).
          </p>
          {loadingFree ? (
            <p className="text-sm text-slate-400">Finding free slots…</p>
          ) : !freeSlots || freeSlots.rooms.length === 0 ? (
            <p className="text-sm text-slate-400">
              No rooms found yet. Rooms appear here once timetable entries include room numbers.
            </p>
          ) : (
            <div className="space-y-3">
              {freeSlots.rooms.map((r) => (
                <div key={r.room} className="rounded-xl border border-slate-100 p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">
                      <DoorClosed className="h-3.5 w-3.5" /> {r.room}
                    </span>
                    {r.free_windows.length === 0 && (
                      <span className="text-xs text-red-500">Fully booked</span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {r.free_windows.map((w, i) => (
                      <button
                        key={i}
                        onClick={() => pickSlot(r.room, w.start, w.end)}
                        className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 transition hover:border-emerald-400 hover:bg-emerald-100"
                      >
                        <Clock className="h-3 w-3" />
                        {fmtTime(w.start)} – {fmtTime(w.end)}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
        )}
        {success && (
          <p className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4" /> {success}
          </p>
        )}

        {/* Check result */}
        {result && (
          <div className="space-y-4">
            {result.has_conflict ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  <h2 className="font-semibold text-slate-900">
                    {result.conflicts.length} conflict{result.conflicts.length !== 1 && "s"} found
                  </h2>
                </div>
                <ul className="mt-3 space-y-2">
                  {result.conflicts.map((c, i) => {
                    const Icon = KIND_ICON[c.kind];
                    return (
                      <li key={i} className="flex items-start gap-2 rounded-lg bg-white/70 px-3 py-2 text-sm text-slate-700">
                        <Icon className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-500" />
                        <span>{c.detail}</span>
                      </li>
                    );
                  })}
                </ul>
                <p className="mt-3 text-xs text-slate-500">
                  Adjust the time, room, or faculty and check again — or schedule anyway if it&apos;s intentional.
                </p>
              </div>
            ) : (
              <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                <ShieldCheck className="h-6 w-6 text-emerald-600" />
                <div>
                  <h2 className="font-semibold text-slate-900">No conflicts — good to schedule ✅</h2>
                  <p className="text-sm text-slate-600">
                    The room, faculty, and batch are all free at this time.
                  </p>
                </div>
              </div>
            )}

            <button
              onClick={handleSchedule}
              disabled={scheduling}
              className={`inline-flex w-full items-center justify-center gap-2 rounded-md py-3 text-sm font-semibold transition disabled:opacity-60 ${
                result.has_conflict
                  ? "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                  : "bg-gradient-to-b from-[#febd69] to-[#ff9900] text-[#131921] hover:brightness-105"
              }`}
            >
              <CalendarPlus className="h-4 w-4" />
              {scheduling
                ? "Scheduling…"
                : result.has_conflict
                ? "Schedule anyway"
                : "Schedule this class"}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
