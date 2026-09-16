import type { OrderTicketsOut } from "@/lib/api";
import TicketQr from "./TicketQr";

export default function TicketList({ order }: { order: OrderTicketsOut }) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900">{order.event_title}</h2>
      <p className="text-sm text-slate-600">
        Commande {order.transaction_id} — {order.tickets.length} billet
        {order.tickets.length > 1 ? "s" : ""}
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        {order.tickets.map((ticket) => (
          <div
            key={ticket.id}
            className="flex flex-col items-center gap-3 rounded-lg border border-slate-200 bg-white p-5 text-center"
          >
            <TicketQr token={ticket.qr_token} />
            <p className="font-medium text-slate-800">{ticket.ticket_type_name}</p>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {ticket.status === "scanne" ? "Déjà scanné" : "Valide"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
