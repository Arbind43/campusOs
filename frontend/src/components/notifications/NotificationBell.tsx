"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell, Pin, X, Megaphone } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { listNotices, Notice } from "@/lib/notices-api";

const SEEN_KEY = "campusos.seenNotices";
const POLL_MS = 60_000;

function loadSeen(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function saveSeen(ids: Set<string>) {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify([...ids]));
  } catch {
    /* ignore */
  }
}

/**
 * Notification bell + toast popup.
 * Polls the notices endpoint (already filtered by the user's department & year
 * on the backend) and pops up any notices the user hasn't seen yet.
 */
export default function NotificationBell() {
  const { token } = useAuthStore();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [open, setOpen] = useState(false);
  const [popup, setPopup] = useState<Notice | null>(null);
  const seenRef = useRef<Set<string>>(new Set());
  const initialized = useRef(false);

  const unreadCount = notices.filter((n) => !seenRef.current.has(n.id)).length;

  const poll = useCallback(async () => {
    try {
      const data = await listNotices();
      setNotices(data);

      // On first load, surface the newest unseen notice as a popup.
      const firstUnseen = data.find((n) => !seenRef.current.has(n.id));
      if (firstUnseen) setPopup(firstUnseen);
    } catch {
      /* silent — notifications are best-effort */
    }
  }, []);

  useEffect(() => {
    if (!token || initialized.current) return;
    initialized.current = true;
    seenRef.current = loadSeen();
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [token, poll]);

  function markAllSeen() {
    const ids = new Set(seenRef.current);
    notices.forEach((n) => ids.add(n.id));
    seenRef.current = ids;
    saveSeen(ids);
    setNotices((prev) => [...prev]); // re-render to clear badge
  }

  function dismissPopup() {
    if (popup) {
      const ids = new Set(seenRef.current);
      ids.add(popup.id);
      seenRef.current = ids;
      saveSeen(ids);
    }
    setPopup(null);
  }

  return (
    <>
      {/* Bell */}
      <div className="relative">
        <button
          onClick={() => {
            setOpen((v) => !v);
            if (!open) markAllSeen();
          }}
          className="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-[#ff9900] hover:text-[#ff9900]"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[#ff9900] px-1 text-[10px] font-bold text-[#131921]">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>

        {/* Dropdown */}
        {open && (
          <div className="absolute right-0 z-30 mt-2 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
              <span className="font-semibold text-slate-900">Notifications</span>
              <button
                onClick={() => setOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notices.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-slate-400">
                  No notifications
                </p>
              ) : (
                notices.slice(0, 12).map((n) => (
                  <div
                    key={n.id}
                    className="flex gap-3 border-b border-slate-50 px-4 py-3 last:border-0"
                  >
                    <span className="mt-0.5 inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#ff9900]/10 text-[#ff9900]">
                      {n.is_pinned ? (
                        <Pin className="h-4 w-4" />
                      ) : (
                        <Megaphone className="h-4 w-4" />
                      )}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {n.title}
                      </p>
                      <p className="line-clamp-2 text-xs text-slate-500">{n.body}</p>
                      <p className="mt-1 text-[11px] text-slate-400">
                        {new Date(n.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
            <Link
              href="/dashboard/notices"
              onClick={() => setOpen(false)}
              className="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-[#b86e00] hover:bg-slate-50"
            >
              View all notices
            </Link>
          </div>
        )}
      </div>

      {/* Toast popup for newest unseen notice */}
      {popup && (
        <div className="fixed bottom-5 right-5 z-50 w-[340px] max-w-[calc(100vw-2.5rem)] animate-in rounded-xl border border-slate-200 bg-white p-4 shadow-2xl">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[#ff9900]/15 text-[#ff9900]">
              <Megaphone className="h-5 w-5" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-[#b86e00]">
                  New Notice
                </span>
                <button
                  onClick={dismissPopup}
                  className="text-slate-400 hover:text-slate-600"
                  aria-label="Dismiss"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-0.5 font-semibold text-slate-900">{popup.title}</p>
              <p className="mt-1 line-clamp-3 text-sm text-slate-600">{popup.body}</p>
              <Link
                href="/dashboard/notices"
                onClick={dismissPopup}
                className="mt-2 inline-block text-sm font-medium text-[#b86e00] hover:underline"
              >
                Read more →
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
