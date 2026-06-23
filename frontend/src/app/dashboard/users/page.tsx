"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { listDepartments, Department } from "@/lib/notices-api";
import {
  listManagedUsers,
  updateManagedUser,
  createDepartment,
  ManagedUser,
} from "@/lib/admin-api";
import { getErrorMessage } from "@/lib/api";
import {
  Users,
  Search,
  Building2,
  Plus,
  CheckCircle2,
  ShieldAlert,
} from "lucide-react";

const ROLES = ["STUDENT", "FACULTY", "ACADEMIC_ADMIN"];

export default function UsersPage() {
  const { user, token } = useAuthStore();
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");

  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // new department form
  const [newDeptName, setNewDeptName] = useState("");
  const [newDeptCode, setNewDeptCode] = useState("");
  const [creatingDept, setCreatingDept] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const [u, d] = await Promise.all([listManagedUsers(), listDepartments()]);
      setUsers(u);
      setDepartments(d);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token && isAdmin) refresh();
    else setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function patchUser(
    id: string,
    field: "department_id" | "year_of_study" | "role",
    value: string
  ) {
    setSavingId(id);
    setSavedId(null);
    setError(null);
    try {
      const body =
        field === "year_of_study"
          ? { year_of_study: value ? Number(value) : null }
          : field === "department_id"
          ? { department_id: value || null }
          : { role: value };
      const updated = await updateManagedUser(id, body);
      setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)));
      setSavedId(id);
      setTimeout(() => setSavedId((cur) => (cur === id ? null : cur)), 1500);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSavingId(null);
    }
  }

  async function handleCreateDept(e: React.FormEvent) {
    e.preventDefault();
    if (!newDeptName || !newDeptCode) return;
    setCreatingDept(true);
    setError(null);
    try {
      const dept = await createDepartment(newDeptName, newDeptCode);
      setDepartments((prev) => [...prev, dept]);
      setNewDeptName("");
      setNewDeptCode("");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCreatingDept(false);
    }
  }

  const filtered = useMemo(() => {
    return users.filter((u) => {
      const matchesSearch =
        !search ||
        u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase());
      const matchesRole = !roleFilter || u.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [users, search, roleFilter]);

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-50">
        <DashboardHeader />
        <main className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white p-10 text-center">
            <ShieldAlert className="h-10 w-10 text-slate-400" />
            <h1 className="text-lg font-bold text-slate-900">Admins only</h1>
            <p className="text-sm text-slate-500">
              You need an administrator role to manage users.
            </p>
          </div>
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
            <Users className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
            <p className="text-sm text-slate-500">
              Assign students to a department and year of study
            </p>
          </div>
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </p>
        )}

        {/* Create department */}
        <form
          onSubmit={handleCreateDept}
          className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-end"
        >
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 sm:mb-2">
            <Building2 className="h-4 w-4 text-[#ff9900]" /> Quick add department
          </div>
          <input
            value={newDeptName}
            onChange={(e) => setNewDeptName(e.target.value)}
            placeholder="Computer Science"
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
          />
          <input
            value={newDeptCode}
            onChange={(e) => setNewDeptCode(e.target.value)}
            placeholder="CSE"
            maxLength={20}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30 sm:w-32"
          />
          <button
            type="submit"
            disabled={creatingDept}
            className="inline-flex items-center justify-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
          >
            <Plus className="h-4 w-4" />
            Add
          </button>
        </form>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name or email…"
              className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
          >
            <option value="">All roles</option>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>

        {/* Users table */}
        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
            No users found.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-4 py-3 font-semibold">User</th>
                    <th className="px-4 py-3 font-semibold">Role</th>
                    <th className="px-4 py-3 font-semibold">Department</th>
                    <th className="px-4 py-3 font-semibold">Year</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <span className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                            {u.full_name.split(" ").slice(0, 2).map((n) => n[0]).join("").toUpperCase()}
                          </span>
                          <div className="min-w-0">
                            <p className="truncate font-medium text-slate-900">{u.full_name}</p>
                            <p className="truncate text-xs text-slate-400">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={u.role}
                          onChange={(e) => patchUser(u.id, "role", e.target.value)}
                          className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-[#ff9900]"
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r.replace("_", " ")}
                            </option>
                          ))}
                          {!ROLES.includes(u.role) && (
                            <option value={u.role}>{u.role}</option>
                          )}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={u.department_id ?? ""}
                          onChange={(e) => patchUser(u.id, "department_id", e.target.value)}
                          className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-[#ff9900]"
                        >
                          <option value="">—</option>
                          {departments.map((d) => (
                            <option key={d.id} value={d.id}>
                              {d.code}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={u.year_of_study ?? ""}
                          onChange={(e) => patchUser(u.id, "year_of_study", e.target.value)}
                          className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-[#ff9900]"
                        >
                          <option value="">—</option>
                          {[1, 2, 3, 4].map((y) => (
                            <option key={y} value={y}>
                              Year {y}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {savingId === u.id ? (
                          <span className="text-xs text-slate-400">Saving…</span>
                        ) : savedId === u.id ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Saved
                          </span>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
