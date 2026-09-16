"use client";

import { Minus, Plus, ShieldCheck, Smartphone } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, createOrder, type TicketType } from "@/lib/api";
import { formatFcfa } from "@/lib/format";

export default function PurchaseForm({
  eventId,
  ticketTypes,
}: {
  eventId: number;
  ticketTypes: TicketType[];
}) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [quantities, setQuantities] = useState<Record<number, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = ticketTypes.reduce((sum, tt) => {
    const qty = quantities[tt.id] ?? 0;
    return sum + qty * Number(tt.price);
  }, 0);

  function setQty(id: number, qty: number) {
    setQuantities((prev) => ({ ...prev, [id]: Math.max(0, Math.min(50, qty)) }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const items = Object.entries(quantities)
      .map(([ticketTypeId, quantity]) => ({ ticket_type_id: Number(ticketTypeId), quantity }))
      .filter((item) => item.quantity > 0);

    if (items.length === 0) {
      setError("Choisissez au moins un billet.");
      return;
    }

    setSubmitting(true);
    try {
      const order = await createOrder({
        event_id: eventId,
        buyer_email: email,
        buyer_phone: phone,
        items,
      });
      if (order.payment_url) {
        // Provider CinetPay réel : redirection vers la page de paiement
        // Mobile Money hébergée par l'agrégateur.
        window.location.href = order.payment_url;
        return;
      }
      // Provider `simulator` (pas d'identifiants CinetPay réels en dev/démo) :
      // la page de commande propose de déclencher le paiement manuellement.
      const params = new URLSearchParams({ email });
      router.push(`/commande/${order.transaction_id}?${params.toString()}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Achat impossible pour le moment.");
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-slate-900">Acheter des billets</h2>

      <div className="space-y-3">
        {ticketTypes.map((tt) => {
          const qty = quantities[tt.id] ?? 0;
          return (
            <div
              key={tt.id}
              className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2.5"
            >
              <div>
                <p className="font-medium text-slate-800">{tt.name}</p>
                <p className="text-sm text-slate-500">{formatFcfa(tt.price)}</p>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  aria-label={`Retirer un billet ${tt.name}`}
                  onClick={() => setQty(tt.id, qty - 1)}
                  className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-300 text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={qty === 0}
                >
                  <Minus className="h-3.5 w-3.5" />
                </button>
                <span className="w-6 text-center text-sm font-semibold text-slate-900">{qty}</span>
                <button
                  type="button"
                  aria-label={`Ajouter un billet ${tt.name}`}
                  onClick={() => setQty(tt.id, qty + 1)}
                  className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-300 text-slate-600 transition hover:bg-slate-100"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="text-slate-700">E-mail</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="vous@example.com"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-700">Téléphone</span>
          <input
            type="tel"
            required
            minLength={8}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="07 00 00 00 00"
          />
        </label>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 pt-4">
        <span className="text-sm text-slate-600">Total</span>
        <span className="text-xl font-bold text-slate-900">{formatFcfa(total)}</span>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <button
        type="submit"
        disabled={submitting || total === 0}
        className="w-full rounded-md bg-gradient-to-br from-indigo-600 to-violet-600 px-4 py-2.5 font-medium text-white shadow-sm transition hover:brightness-110 disabled:cursor-not-allowed disabled:from-slate-300 disabled:to-slate-300 disabled:shadow-none"
      >
        {submitting ? "Traitement..." : "Commander"}
      </button>

      <div className="flex items-center justify-center gap-4 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Smartphone className="h-3.5 w-3.5" /> Mobile Money
        </span>
        <span className="flex items-center gap-1">
          <ShieldCheck className="h-3.5 w-3.5" /> Billet QR sécurisé
        </span>
      </div>
    </form>
  );
}
