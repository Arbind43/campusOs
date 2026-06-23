"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import { AlertCircle, RefreshCw, Upload, CalendarDays, Info } from "lucide-react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import TimetableUploader from "@/components/timetable/TimetableUploader";
import TimetableDisplay from "@/components/timetable/TimetableDisplay";
import { getTimetable, TimetableEntry } from "@/lib/timetable-api";

export default function TimetablePage() {
  const { user, token } = useAuthStore();
  const [entries, setEntries] = useState<TimetableEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editingEntries, setEditingEntries] = useState<TimetableEntry[]>([]);

  const isAcademicAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");

  const loadTimetable = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await getTimetable();
      setEntries(data);
      setIsEditing(false);
    } catch (err) {
      console.error("Failed to load timetable:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (entriesToEdit: TimetableEntry[]) => {
    setEditingEntries(entriesToEdit);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingEntries([]);
  };

  useEffect(() => {
    if (token) loadTimetable();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader />

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
        {/* Title */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[#ff9900]/10 text-[#ff9900]">
              <CalendarDays className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {isAcademicAdmin ? "Update Timetable" : "Timetable"}
              </h1>
              <p className="text-sm text-slate-500">
                {isAcademicAdmin
                  ? "Upload a photo and let AI organize the schedule"
                  : "Your class schedule"}
              </p>
            </div>
          </div>
          <button
            onClick={loadTimetable}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-[#ff9900] hover:text-[#b86e00] disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {!user ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
            Loading your profile…
          </div>
        ) : (
          <>
            {/* Upload (admin) */}
            {isAcademicAdmin && !isEditing && (
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center gap-2">
                  <Upload className="h-5 w-5 text-[#ff9900]" />
                  <h2 className="font-semibold text-slate-900">Upload Timetable</h2>
                </div>
                <p className="mb-4 text-sm text-slate-500">
                  Upload a photo of the timetable. Our AI extracts and organizes the
                  classes for review before saving.
                </p>
                <TimetableUploader
                  onSuccess={(newEntries) => {
                    setEntries(newEntries);
                    loadTimetable();
                  }}
                />
              </section>
            )}

            {!isAcademicAdmin && (
              <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" />
                <div className="text-sm text-amber-800">
                  <p className="font-medium">Timetable is managed by your academic office</p>
                  <p className="mt-1">
                    You can view the schedule below. Contact an Academic Admin for changes.
                  </p>
                </div>
              </div>
            )}

            {/* Edit (admin) */}
            {isAcademicAdmin && isEditing && (
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="mb-1 font-semibold text-slate-900">Edit Timetable</h2>
                <p className="mb-4 text-sm text-slate-500">
                  Modify entries. Changes replace the current timetable.
                </p>
                <TimetableUploader
                  initialEntries={editingEntries}
                  onSuccess={(newEntries) => {
                    setEntries(newEntries);
                    loadTimetable();
                  }}
                  onCancel={handleCancelEdit}
                />
              </section>
            )}

            {/* Display */}
            {!isEditing && (
              <section className="space-y-4">
                <h2 className="text-lg font-bold text-slate-900">Your Schedule</h2>
                {loading ? (
                  <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
                    Loading timetable…
                  </div>
                ) : (
                  <TimetableDisplay
                    entries={entries}
                    isAdmin={isAcademicAdmin}
                    onEdit={handleEdit}
                  />
                )}
              </section>
            )}

            {/* Info */}
            <section className="flex gap-3 rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
              <Info className="mt-0.5 h-5 w-5 flex-shrink-0 text-blue-600" />
              <div className="space-y-1.5 text-sm text-blue-800">
                <p>
                  <strong>Academic Admin:</strong> uploads timetable photos that are auto-parsed
                  and organized.
                </p>
                <p>
                  <strong>Students:</strong> view the schedule here, on the dashboard, and in AI
                  daily briefings.
                </p>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
