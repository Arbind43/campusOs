"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import {
  listNotices,
  createNotice,
  deleteNotice,
  listDepartments,
  Notice,
  Department,
} from "@/lib/notices-api";
import { getErrorMessage } from "@/lib/api";
import {
  Megaphone,
  Pin,
  Trash2,
  Send,
  CheckCircle2,
  Building2,
  GraduationCap,
} from "lucide-react";

export default function NoticesPage() {
  const { user, token } = useAuthStore();
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");

  const [notices, setNotices] = useState<Notice[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  // form state
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [deptId, setDeptId] = useState<string>("");
  const [year, setYear] = useState<string>("");
  const [pinned, setPinned] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const data = await listNotices("academic");
      setNotices(data);
    } catch (err) {
      console.error("Failed to load notices", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) return;
    refresh();
    if (isAdmin) {
      listDepartments()
        .then(setDepartments)
        .catch(() => setDepartments([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      await createNotice({
        title,
        body,
        domain: "academic",
        target_department_id: deptId || null,
        target_year: year ? Number(year) : null,
        is_pinned: pinned,
      });
      setSuccess("Notice published. Students will be notified.");
      setTitle("");
      setBody("");
      setYear("");
      setPinned(false);
      refresh();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteNotice(id);
      setNotices((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      console.error("Failed to delete", err);
    }
  }

  function deptName(id: string | null) {
    if (!id) return "All Departments";
    return departments.find((d) => d.id === id)?.name ?? "Department";
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
            <Megaphone className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Notices</h1>
            <p className="text-sm text-slate-500">
              {isAdmin
                ? "Publish announcements targeted by department and year"
                : "Latest announcements for you"}
            </p>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-5">
          {/* Create form (admin only) */}
          {isAdmin && (
            <div className="lg:col-span-2">
              <form
                onSubmit={handleSubmit}
                className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <h2 className="font-semibold text-slate-900">Create Notice</h2>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Title</label>
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    maxLength={255}
                    placeholder="Mid-term exam schedule released"
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Message</label>
                  <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    required
                    rows={4}
                    placeholder="Write the announcement details…"
                    className="w-full resize-none rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
                      <Building2 className="h-3.5 w-3.5" /> Department
                    </label>
                    <select
                      value={deptId}
                      onChange={(e) => setDeptId(e.target.value)}
                      className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
                    >
                      <option value="">All Departments</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
                      <GraduationCap className="h-3.5 w-3.5" /> Year
                    </label>
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
                </div>

                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={pinned}
                    onChange={(e) => setPinned(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 accent-[#ff9900]"
                  />
                  <Pin className="h-3.5 w-3.5" /> Pin to top
                </label>

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

                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] py-2.5 text-sm font-semibold text-[#131921] shadow-sm transition hover:brightness-105 disabled:opacity-60"
                >
                  <Send className="h-4 w-4" />
                  {submitting ? "Publishing…" : "Publish Notice"}
                </button>
              </form>
            </div>
          )}

          {/* Notices list */}
          <div className={isAdmin ? "lg:col-span-3" : "lg:col-span-5"}>
            <h2 className="mb-3 font-semibold text-slate-900">Published Notices</h2>
            {loading ? (
              <p className="text-sm text-slate-400">Loading…</p>
            ) : notices.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
                No notices yet.
              </div>
            ) : (
              <div className="space-y-3">
                {notices.map((n) => (
                  <div
                    key={n.id}
                    className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        {n.is_pinned && (
                          <Pin className="h-4 w-4 flex-shrink-0 text-[#ff9900]" />
                        )}
                        <h3 className="font-semibold text-slate-900">{n.title}</h3>
                      </div>
                      {isAdmin && (
                        <button
                          onClick={() => handleDelete(n.id)}
                          className="rounded-md p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-600"
                          aria-label="Delete notice"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">
                      {n.body}
                    </p>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                      <span className="rounded-full bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
                        {deptName(n.target_department_id)}
                      </span>
                      <span className="rounded-full bg-purple-50 px-2 py-0.5 font-medium text-purple-700">
                        {n.target_year ? `Year ${n.target_year}` : "All Years"}
                      </span>
                      <span className="text-slate-400">
                        {new Date(n.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
