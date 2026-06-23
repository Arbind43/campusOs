"use client";

import { useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { askAssistant, getChatHistory, clearChatHistory } from "@/lib/assistant-api";
import { getErrorMessage } from "@/lib/api";
import { Sparkles, Send, Bot, User, CalendarDays, Utensils, BarChart3, HelpCircle, Trash2, Bell } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  text: string;
}

const STUDENT_SUGGESTIONS = [
  { icon: CalendarDays, text: "What is my schedule today?" },
  { icon: Utensils, text: "What is the mess menu and timing?" },
  { icon: BarChart3, text: "What is my attendance?" },
  { icon: HelpCircle, text: "Can I miss my next class?" },
];

const ADMIN_SUGGESTIONS = [
  { icon: Bell, text: "Post a notice that tomorrow is a holiday" },
  { icon: CalendarDays, text: "Put Bengali class on Monday 7 pm" },
  { icon: CalendarDays, text: "Cancel Bengali class on Monday" },
  { icon: HelpCircle, text: "What is on the timetable this week?" },
];

export default function AssistantPage() {
  return (
    <Suspense fallback={null}>
      <AssistantInner />
    </Suspense>
  );
}

function AssistantInner() {
  const { user, token } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [clearing, setClearing] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  // Load saved conversation on mount
  useEffect(() => {
    if (!token) {
      setLoadingHistory(false);
      return;
    }
    getChatHistory()
      .then((rows) =>
        setMessages(rows.map((r) => ({ role: r.role, text: r.content })))
      )
      .catch(() => setMessages([]))
      .finally(() => setLoadingHistory(false));
  }, [token]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-send a question passed via ?q= (from digest quick-actions)
  const searchParams = useSearchParams();
  const autoSent = useRef(false);
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !loadingHistory && !autoSent.current) {
      autoSent.current = true;
      send(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadingHistory, searchParams]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await askAssistant(q);
      setMessages((prev) => [...prev, { role: "assistant", text: res.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Sorry, something went wrong: ${getErrorMessage(err)}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    setClearing(true);
    try {
      await clearChatHistory();
      setMessages([]);
    } catch (err) {
      console.error(err);
    } finally {
      setClearing(false);
    }
  }

  const firstName = user?.full_name?.split(" ")[0] ?? "there";
  const isAdmin =
    user?.role === "ACADEMIC_ADMIN" ||
    user?.role === "SUPER_ADMIN" ||
    user?.roles?.includes("ACADEMIC_ADMIN") ||
    user?.roles?.includes("SUPER_ADMIN");
  const suggestions = isAdmin ? ADMIN_SUGGESTIONS : STUDENT_SUGGESTIONS;

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <DashboardHeader />

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-6 sm:px-6">
        {/* Title */}
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-b from-[#febd69] to-[#ff9900] text-[#131921]">
              <Sparkles className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Campus Assistant</h1>
              <p className="text-sm text-slate-500">
                {isAdmin
                  ? "Ask questions or run commands (notices, timetable)"
                  : "Ask about your schedule, attendance, mess, and notices"}
              </p>
            </div>
          </div>
          {messages.length > 0 && (
            <button
              onClick={handleClear}
              disabled={clearing}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition hover:border-red-300 hover:text-red-600 disabled:opacity-60"
            >
              <Trash2 className="h-4 w-4" />
              <span className="hidden sm:inline">{clearing ? "Clearing…" : "Clear"}</span>
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
          {loadingHistory ? (
            <div className="flex h-full items-center justify-center py-10 text-sm text-slate-400">
              Loading your conversation…
            </div>
          ) : messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center py-10 text-center">
              <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[#ff9900]/10 text-[#ff9900]">
                <Bot className="h-7 w-7" />
              </div>
              <h2 className="text-lg font-semibold text-slate-900">
                Hi {firstName}, how can I help?
              </h2>
              <p className="mt-1 max-w-sm text-sm text-slate-500">
                {isAdmin
                  ? "Ask about campus data, or give commands like \u201cpost a notice\u201d or \u201cadd a class\u201d."
                  : "I can answer using your timetable, attendance, mess menu, and notices."}
              </p>
              <div className="mt-6 grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
                {suggestions.map(({ icon: Icon, text }) => (
                  <button
                    key={text}
                    onClick={() => send(text)}
                    className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left text-sm text-slate-700 transition hover:border-[#ff9900] hover:bg-[#ff9900]/5"
                  >
                    <Icon className="h-4 w-4 flex-shrink-0 text-[#ff9900]" />
                    {text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div
                key={i}
                className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <span
                  className={`inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
                    m.role === "user"
                      ? "bg-slate-900 text-white"
                      : "bg-[#ff9900]/15 text-[#ff9900]"
                  }`}
                >
                  {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </span>
                <div
                  className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
                    m.role === "user"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-800"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex gap-3">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#ff9900]/15 text-[#ff9900]">
                <Bot className="h-4 w-4" />
              </span>
              <div className="flex items-center gap-1 rounded-2xl bg-slate-100 px-4 py-3">
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="mt-4 flex items-center gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your campus life…"
            className="flex-1 rounded-full border border-slate-300 bg-white px-5 py-3 text-sm outline-none focus:border-[#ff9900] focus:ring-2 focus:ring-[#ff9900]/30"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="inline-flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-b from-[#febd69] to-[#ff9900] text-[#131921] shadow-md transition hover:brightness-105 disabled:opacity-50"
            aria-label="Send"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </main>
    </div>
  );
}
