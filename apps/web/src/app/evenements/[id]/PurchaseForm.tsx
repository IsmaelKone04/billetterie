"use client";

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
    <form onSubmit={handleSubmit} className="space-y-5 rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold text-slate-900">Acheter des billets</h2>

      <div className="space-y-3">
        {ticketTypes.map((tt) => (
          <div key={tt.id} className="flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-slate-800">{tt.name}</p>
              <p className="text-sm text-slate-500">{formatFcfa(tt.price)}</p>
            </div>
            <input
              type="number"
              min={0}
              max={50}
              value={quantities[tt.id] ?? 0}
              onChange={(e) =>
                setQuantities((prev) => ({ ...prev, [tt.id]: Number(e.target.value) }))
              }
              className="w-20 rounded-md border border-slate-300 px-2 py-1.5 text-right"
            />
          </div>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="text-slate-700">E-mail</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
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
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="07 00 00 00 00"
          />
        </label>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 pt-4">
        <span className="text-sm text-slate-600">Total</span>
        <span className="text-lg font-semibold text-slate-900">{formatFcfa(total)}</span>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <button
        type="submit"
        disabled={submitting || total === 0}
        className="w-full rounded-md bg-indigo-600 px-4 py-2.5 font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {submitting ? "Traitement..." : "Commander"}
      </button>
    </form>
  );
}
