import { apiClient } from "./api";

export interface Ticket {
  id: string;
  title: string;
  description: string;
  category: "Maintenance" | "IT Support" | "General";
  status: "Open" | "In Progress" | "Resolved" | "Closed";
  priority: "Low" | "Medium" | "High";
  location?: string | null;
  created_by: string;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
  creator_name?: string;
  creator_role?: string;
}

export interface TicketCreate {
  title: string;
  description: string;
  category: "Maintenance" | "IT Support" | "General";
  priority: "Low" | "Medium" | "High";
  location?: string;
}

export interface TicketUpdate {
  status?: "Open" | "In Progress" | "Resolved" | "Closed";
  priority?: "Low" | "Medium" | "High";
  assigned_to?: string;
}

export const helpdeskApi = {
  createTicket: (data: TicketCreate) => 
    apiClient.post<Ticket>("/helpdesk/tickets", data),
    
  getTickets: () => 
    apiClient.get<Ticket[]>("/helpdesk/tickets"),
    
  updateTicket: (id: string, data: TicketUpdate) => 
    apiClient.patch<Ticket>(`/helpdesk/tickets/${id}`, data),
};
