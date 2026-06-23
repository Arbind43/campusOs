"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import {
  listDrives,
  createDrive,
  deleteDrive,
  registerForDrive,
  listPlacementNotices,
  createPlacementNotice,
  deletePlacementNotice,
  PlacementDrive,
  PlacementNotice,
} from "@/lib/placement-api";
import { getErrorMessage } from "@/lib/api";
import {
  Briefcase,
  Building2,
  Trash2,
  Send,
  CheckCircle2,
  CalendarClock,
  IndianRupee,
  BookOpen,
  Plus,
} from "lucide-react";

export default function PlacementPage() {
  const { user, token } = useAuthStore();
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN") ||
    user?.roles?.includes("PLACEMENT_ADMIN") ||
    user?.roles?.includes("PLACEMENT_COORDINATOR");

  const [drives, setDrives] = useState<PlacementDrive[]>([]);
  const [notices, setNotices] = useState<PlacementNotice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // drive form
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [pkg, setPkg] = useState("");
  const [driveDate, setDriveDate] = useState("");
  const [deadline, setDeadline] = useState("");
  const [desc, setDesc] = useState("");
  const [savingDrive, setSavingDrive] = useState(false);

  // notice form
  const [nTitle, setNTitle] = useState("");
  const [nBody, setNBody] = useState("");
  const [savingNotice, setSavingNotice] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const [d, n] = await Promise.all([
        listDrives(isAdmin ? false : true),
        listPlacementNotices(),
      ]);
      setDrives(d);
      setNotices(n);
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

  async function handleCreateDrive(e: React.FormEvent) {
    e.preventDefault();
    setSavingDrive(true);
    setError(null);
    setSuccess(null);
    try {
      await createDrive({
        company_name: company,
        job_role: role,
        package_lpa: pkg ? Number(pkg) : null,
        drive_date: driveDate || null,
        registration_deadline: deadline || null,
        description: desc,
      });
      setSuccess("Placement drive published.");
      setCompany(""); setRole(""); setPkg(""); setDriveDate(""); setDeadline(""); setDesc("");
      refresh();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingDrive(false);
    }
  }

  async function handleCreateNotice(e: React.FormEvent) {
    e.preventDefault();
    setSavingNotice(true);
    setError(null);
    setSuccess(null);
    try {
      await createPlacementNotice({ title: nTitle, body: nBody });
      setSuccess("Placement info posted.");
      setNTitle(""); setNBody("");
      refresh();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingNotice(false);
    }
  }

  async function handleRegister(id: string) {
    setError(null);
    setSuccess(null);
    try {
      const res = await registerForDrive(id);
      setSuccess(res.message);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  const inputCls =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30";

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />
      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
            <Briefcase className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Placements</h1>
            <p className="text-sm text-slate-500">
              {isAdmin
                ? "Post drives and placement preparation resources"
                : "Drives, opportunities & prep resources"}
            </p>
          </div>
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
        )}
        {success && (
          <p className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4" /> {success}
          </p>
        )}

        {/* Admin forms */}
        {isAdmin && (
          <div className="grid gap-6 lg:grid-cols-2">
            <form onSubmit={handleCreateDrive} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="flex items-center gap-2 font-semibold text-slate-900">
                <Building2 className="h-4 w-4 text-[#ff9900]" /> New Drive
              </h2>
              <div className="grid grid-cols-2 gap-3">
                <input value={company} onChange={(e) => setCompany(e.target.value)} required placeholder="Company" className={inputCls} />
                <input value={role} onChange={(e) => setRole(e.target.value)} required placeholder="Job role" className={inputCls} />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <input value={pkg} onChange={(e) => setPkg(e.target.value)} type="number" step="0.1" min="0" placeholder="LPA" className={inputCls} />
                <div>
                  <label className="text-xs text-slate-500">Drive date</label>
                  <input value={driveDate} onChange={(e) => setDriveDate(e.target.value)} type="date" className={inputCls} />
                </div>
                <div>
                  <label className="text-xs text-slate-500">Apply by</label>
                  <input value={deadline} onChange={(e) => setDeadline(e.target.value)} type="date" className={inputCls} />
                </div>
              </div>
              <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={3} placeholder="Eligibility, rounds, details…" className={`${inputCls} resize-none`} />
              <button type="submit" disabled={savingDrive} className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] py-2.5 text-sm font-semibold text-[#131921] transition hover:brightness-105 disabled:opacity-60">
                <Plus className="h-4 w-4" /> {savingDrive ? "Publishing…" : "Publish Drive"}
              </button>
            </form>

            <form onSubmit={handleCreateNotice} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="flex items-center gap-2 font-semibold text-slate-900">
                <BookOpen className="h-4 w-4 text-[#ff9900]" /> Placement Info / Prep Resource
              </h2>
              <input value={nTitle} onChange={(e) => setNTitle(e.target.value)} required placeholder="Title (e.g. DSA prep sheet, resume tips)" className={inputCls} />
              <textarea value={nBody} onChange={(e) => setNBody(e.target.value)} required rows={5} placeholder="Resource details, links, guidelines…" className={`${inputCls} resize-none`} />
              <button type="submit" disabled={savingNotice} className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-slate-900 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60">
                <Send className="h-4 w-4" /> {savingNotice ? "Posting…" : "Post Info"}
              </button>
            </form>
          </div>
        )}

        {/* Drives */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Placement Drives</h2>
          {loading ? (
            <p className="text-sm text-slate-400">Loading…</p>
          ) : drives.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
              No placement drives yet.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {drives.map((d) => (
                <div key={d.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-900">{d.company_name}</h3>
                      <p className="text-sm text-slate-500">{d.job_role}</p>
                    </div>
                    {isAdmin && (
                      <button onClick={() => deleteDrive(d.id).then(refresh)} className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600" aria-label="Delete">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs">
                    {d.package_lpa != null && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
                        <IndianRupee className="h-3 w-3" />{d.package_lpa} LPA
                      </span>
                    )}
                    {d.registration_deadline && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 font-medium text-amber-700">
                        <CalendarClock className="h-3 w-3" /> Apply by {d.registration_deadline}
                      </span>
                    )}
                    {d.drive_date && (
                      <span className="rounded-full bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
                        Drive: {d.drive_date}
                      </span>
                    )}
                  </div>
                  {d.description && <p className="mt-2 text-sm text-slate-600">{d.description}</p>}
                  {!isAdmin && (
                    <button onClick={() => handleRegister(d.id)} className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-gradient-to-b from-[#febd69] to-[#ff9900] px-4 py-2 text-sm font-semibold text-[#131921] transition hover:brightness-105">
                      Register
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Prep resources / info */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Info & Preparation</h2>
          {notices.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
              No placement resources posted yet.
            </div>
          ) : (
            <div className="space-y-3">
              {notices.map((n) => (
                <div key={n.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="flex items-center gap-2 font-semibold text-slate-900">
                      <BookOpen className="h-4 w-4 text-[#ff9900]" /> {n.title}
                    </h3>
                    {isAdmin && (
                      <button onClick={() => deletePlacementNotice(n.id).then(refresh)} className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600" aria-label="Delete">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600">{n.body}</p>
                  <p className="mt-2 text-xs text-slate-400">{new Date(n.created_at).toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
