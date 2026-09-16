"use client";

import { Calendar, CheckCircle2, Download, MapPin } from "lucide-react";
import { useState } from "react";
import type { OrderTicketsOut, TicketOut } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { downloadTicketPdf } from "@/lib/ticketPdf";
import TicketQr from "./TicketQr";

function TicketCard({ order, ticket }: { order: OrderTicketsOut; ticket: TicketOut }) {
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    setDownloading(true);
    try {
      await downloadTicketPdf(order, ticket);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-1 flex-col gap-1.5 p-5">
        <p className="font-semibold text-slate-900">{ticket.ticket_type_name}</p>
        {ticket.seat_label && (
          <span className="w-fit rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700">
            Siège {ticket.seat_label}
          </span>
        )}
        <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
          <Calendar className="h-3.5 w-3.5 shrink-0" />
          {formatDateTime(order.event_starts_at)}
        </p>
        <p className="flex items-center gap-1.5 text-xs text-slate-500">
          <MapPin className="h-3.5 w-3.5 shrink-0" />
          {order.venue.name} — {order.venue.city}
        </p>

        <p
          className={`mt-2 flex w-fit items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
            ticket.status === "scanne"
              ? "bg-slate-100 text-slate-500"
              : "bg-green-50 text-green-700"
          }`}
        >
          <CheckCircle2 className="h-3 w-3" />
          {ticket.status === "scanne" ? "Déjà scanné" : "Valide"}
        </p>

        <button
          onClick={handleDownload}
          disabled={downloading}
          className="mt-3 flex w-fit items-center gap-1.5 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
        >
          <Download className="h-3.5 w-3.5" />
          {downloading ? "Génération..." : "Télécharger (PDF)"}
        </button>
      </div>

      <div className="flex flex-col items-center justify-center gap-2 border-l border-dashed border-slate-200 bg-slate-50 p-4">
        <TicketQr token={ticket.qr_token} />
      </div>
    </div>
  );
}

export default function TicketList({ order }: { order: OrderTicketsOut }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{order.event_title}</h2>
        <p className="text-sm text-slate-600">
          Commande <span className="font-mono">{order.transaction_id}</span> —{" "}
          {order.tickets.length} billet
          {order.tickets.length > 1 ? "s" : ""}
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {order.tickets.map((ticket) => (
          <TicketCard key={ticket.id} order={order} ticket={ticket} />
        ))}
      </div>
    </div>
  );
}
