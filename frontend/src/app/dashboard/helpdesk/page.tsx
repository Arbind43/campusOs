"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import { helpdeskApi, Ticket, TicketCreate, TicketUpdate } from "@/lib/helpdesk-api";
import { getErrorMessage } from "@/lib/api";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Plus,
  Wrench,
  Monitor,
  MessageSquare,
  X,
  MapPin,
  Tag,
  Loader2
} from "lucide-react";

const priorityColors = {
  Low: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  Medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  High: "bg-red-500/10 text-red-400 border-red-500/20",
};

const statusIcons = {
  Open: <AlertCircle className="w-4 h-4 text-orange-400" />,
  "In Progress": <Clock className="w-4 h-4 text-blue-400" />,
  Resolved: <CheckCircle2 className="w-4 h-4 text-green-400" />,
  Closed: <CheckCircle2 className="w-4 h-4 text-gray-400" />,
};

const categoryIcons = {
  Maintenance: <Wrench className="w-4 h-4" />,
  "IT Support": <Monitor className="w-4 h-4" />,
  General: <MessageSquare className="w-4 h-4" />,
};

export default function HelpdeskPage() {
  const { user } = useAuthStore();
  const isAdmin = user?.role === "ACADEMIC_ADMIN";

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Form State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<"Maintenance" | "IT Support" | "General">("Maintenance");
  const [priority, setPriority] = useState<"Low" | "Medium" | "High">("Medium");
  const [location, setLocation] = useState("");

  useEffect(() => {
    fetchTickets();
  }, []);

  async function fetchTickets() {
    try {
      setLoading(true);
      const res = await helpdeskApi.getTickets();
      setTickets(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTicket(e: React.FormEvent) {
    e.preventDefault();
    try {
      await helpdeskApi.createTicket({
        title,
        description,
        category,
        priority,
        location: location || undefined,
      });
      setIsModalOpen(false);
      setTitle("");
      setDescription("");
      setLocation("");
      fetchTickets();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  }

  async function updateStatus(id: string, newStatus: TicketUpdate["status"]) {
    try {
      await helpdeskApi.updateTicket(id, { status: newStatus });
      fetchTickets();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  }

  const columns = ["Open", "In Progress", "Resolved"];

  return (
    <div className="p-6 pb-24 md:pb-6">
      <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Campus Helpdesk</h1>
          <p className="text-white/60">Report and track maintenance & IT issues.</p>
        </div>
        {!isAdmin && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#febd69] to-[#ff9900] px-4 py-2.5 text-sm font-semibold text-[#131921] shadow-lg shadow-[#ff9900]/20 transition-all hover:scale-[1.02] hover:shadow-[#ff9900]/30"
          >
            <Plus className="w-4 h-4" />
            New Ticket
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[#ff9900]" />
        </div>
      ) : isAdmin ? (
        // ADMIN KANBAN BOARD
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {columns.map((col) => (
            <div key={col} className="flex flex-col gap-4 rounded-2xl bg-white/5 p-4 border border-white/10">
              <h3 className="flex items-center gap-2 font-semibold text-white">
                {statusIcons[col as keyof typeof statusIcons]}
                {col}
                <span className="ml-auto flex h-6 w-6 items-center justify-center rounded-full bg-white/10 text-xs">
                  {tickets.filter((t) => t.status === col).length}
                </span>
              </h3>
              <div className="flex flex-col gap-3">
                {tickets
                  .filter((t) => t.status === col)
                  .map((ticket) => (
                    <div key={ticket.id} className="group relative flex flex-col gap-3 rounded-xl border border-white/10 bg-[#131921] p-4 transition-all hover:border-[#ff9900]/50 hover:shadow-lg hover:shadow-[#ff9900]/10">
                      <div className="flex items-start justify-between gap-2">
                        <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium ${priorityColors[ticket.priority as keyof typeof priorityColors]}`}>
                          {ticket.priority}
                        </span>
                        <select
                          value={ticket.status}
                          onChange={(e) => updateStatus(ticket.id, e.target.value as any)}
                          className="bg-white/5 border border-white/10 text-xs text-white rounded-md px-2 py-1 outline-none focus:border-[#ff9900]"
                        >
                          <option value="Open">Open</option>
                          <option value="In Progress">In Progress</option>
                          <option value="Resolved">Resolved</option>
                          <option value="Closed">Closed</option>
                        </select>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold text-white">{ticket.title}</h4>
                        <p className="mt-1 line-clamp-2 text-sm text-white/60">{ticket.description}</p>
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-white/40">
                        <div className="flex items-center gap-1.5">
                          <Tag className="w-3.5 h-3.5" />
                          {ticket.category}
                        </div>
                        {ticket.location && (
                          <div className="flex items-center gap-1.5">
                            <MapPin className="w-3.5 h-3.5" />
                            {ticket.location}
                          </div>
                        )}
                      </div>
                      <div className="mt-2 pt-2 border-t border-white/5 text-xs text-white/50 flex justify-between">
                        <span>{ticket.creator_name}</span>
                        <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        // STUDENT LIST VIEW
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tickets.length === 0 ? (
            <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-4 rounded-full bg-white/5 p-4">
                <MessageSquare className="h-8 w-8 text-white/20" />
              </div>
              <h3 className="text-lg font-medium text-white">No tickets yet</h3>
              <p className="mt-1 text-sm text-white/50">You haven't submitted any helpdesk requests.</p>
            </div>
          ) : (
            tickets.map((ticket) => (
              <div key={ticket.id} className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-5 transition-all hover:border-white/20">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${priorityColors[ticket.priority as keyof typeof priorityColors]}`}>
                        {ticket.priority}
                      </span>
                      <span className="flex items-center gap-1.5 text-xs font-medium text-white/70">
                        {statusIcons[ticket.status as keyof typeof statusIcons]}
                        {ticket.status}
                      </span>
                    </div>
                    <h3 className="font-semibold text-white">{ticket.title}</h3>
                  </div>
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5 text-white/60">
                    {categoryIcons[ticket.category as keyof typeof categoryIcons]}
                  </div>
                </div>

                <p className="text-sm text-white/60">{ticket.description}</p>

                {ticket.location && (
                  <div className="flex items-center gap-2 text-sm text-white/50">
                    <MapPin className="w-4 h-4" />
                    {ticket.location}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* CREATE TICKET MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-[#131921] shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-6 py-4">
              <h3 className="text-lg font-semibold text-white">Submit New Request</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-white/40 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateTicket} className="flex flex-col gap-4 p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/80">Category</label>
                  <select
                    value={category}
                    onChange={(e: any) => setCategory(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-[#ff9900]"
                  >
                    <option value="Maintenance">Maintenance</option>
                    <option value="IT Support">IT Support</option>
                    <option value="General">General</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/80">Priority</label>
                  <select
                    value={priority}
                    onChange={(e: any) => setPriority(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-[#ff9900]"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/80">Title</label>
                <input
                  required
                  type="text"
                  placeholder="e.g., AC not working in Room 204"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-[#ff9900]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/80">Location (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g., Hostel A, Room 204"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-[#ff9900]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-white/80">Description</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Please describe the issue in detail..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full resize-none rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-[#ff9900]"
                />
              </div>

              <div className="mt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 rounded-xl bg-white/5 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-xl bg-gradient-to-r from-[#febd69] to-[#ff9900] px-4 py-2.5 text-sm font-semibold text-[#131921] shadow-lg shadow-[#ff9900]/20 hover:scale-[1.02]"
                >
                  Submit Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
