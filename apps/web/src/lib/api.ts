// Client HTTP vers l'API publique FastAPI (apps/api-fastapi). Toutes les
// requêtes passent par cette fonction pour centraliser la gestion d'erreur
// et l'URL de base — jamais d'URL FastAPI en dur ailleurs dans le code.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Corps non-JSON (ou vide) : on garde le statusText.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type Venue = { name: string; city: string };

export type EventListItem = {
  id: number;
  title: string;
  starts_at: string;
  venue: Venue;
  organizer_display_name: string;
};

export type TicketType = { id: number; name: string; price: string; quota: number };

export type EventDetail = EventListItem & {
  description: string;
  ticket_types: TicketType[];
};

export type OrderCreateOut = {
  order_id: number;
  transaction_id: string;
  status: string;
  amount_total: string;
  payment_url: string | null;
};

export type TicketOut = { id: number; ticket_type_name: string; status: string; qr_token: string };

export type OrderTicketsOut = {
  transaction_id: string;
  status: string;
  event_title: string;
  tickets: TicketOut[];
};

export type ScanOut = {
  ticket_id: number;
  ticket_type_name: string;
  event_title: string;
  scanned_at: string;
};

export type OrganizerAuthOut = { access_token: string; token_type: string };
export type OrganizerMeOut = { id: number; display_name: string; email: string };

export type EventAnalyticsOut = {
  event_id: number;
  title: string;
  status: string;
  tickets_sold: number;
  quota_total: number;
  fill_rate: number;
  revenue: string;
};

export type OrganizerDashboardOut = {
  organizer_id: number;
  display_name: string;
  total_events: number;
  total_tickets_sold: number;
  total_revenue: string;
  events: EventAnalyticsOut[];
};

export const getEvents = () => request<EventListItem[]>("/events");

export const getEvent = (id: number) => request<EventDetail>(`/events/${id}`);

export const createOrder = (payload: {
  event_id: number;
  buyer_email: string;
  buyer_phone: string;
  items: { ticket_type_id: number; quantity: number }[];
}) => request<OrderCreateOut>("/orders", { method: "POST", body: JSON.stringify(payload) });

export const simulatePayment = (transactionId: string, outcome: "success" | "failed") =>
  request<{ outcome: string }>("/payments/simulate", {
    method: "POST",
    body: JSON.stringify({ transaction_id: transactionId, outcome }),
  });

export const getOrderTickets = (transactionId: string, email: string) =>
  request<OrderTicketsOut>(
    `/orders/${encodeURIComponent(transactionId)}/tickets?email=${encodeURIComponent(email)}`
  );

export const scanTicket = (qrToken: string, scanKey: string) =>
  request<ScanOut>("/scan", {
    method: "POST",
    headers: { "X-Scan-Key": scanKey },
    body: JSON.stringify({ qr_token: qrToken }),
  });

export const organizerSignup = (payload: {
  display_name: string;
  email: string;
  password: string;
  phone?: string;
  mobile_money_account?: string;
}) => request<OrganizerAuthOut>("/organizers/signup", { method: "POST", body: JSON.stringify(payload) });

export const organizerLogin = (payload: { email: string; password: string }) =>
  request<OrganizerAuthOut>("/organizers/login", { method: "POST", body: JSON.stringify(payload) });

export const organizerMe = (token: string) =>
  request<OrganizerMeOut>("/organizers/me", { headers: { Authorization: `Bearer ${token}` } });

export const organizerDashboard = (token: string) =>
  request<OrganizerDashboardOut>("/organizers/me/dashboard", {
    headers: { Authorization: `Bearer ${token}` },
  });
