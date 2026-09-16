"use client";

import { useState } from "react";
import { ApiError, getOrderTickets, type OrderTicketsOut } from "@/lib/api";
import TicketList from "@/components/TicketList";

export default function MesBilletsPage() {
  const [transactionId, setTransactionId] = useState("");
  const [email, setEmail] = useState("");
  const [order, setOrder] = useState<OrderTicketsOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setOrder(null);
    try {
      const data = await getOrderTickets(transactionId.trim(), email.trim());
      setOrder(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de contacter l'API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Mes billets</h1>
        <p className="mt-1 text-slate-600">
          Retrouvez vos billets avec le numéro de commande et l&apos;e-mail utilisés à l&apos;achat.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
        <label className="block text-sm">
          <span className="text-slate-700">Numéro de commande</span>
          <input
            required
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="BILLETTERIE-..."
          />
        </label>
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
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-indigo-600 px-4 py-2.5 font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
        >
          {loading ? "Recherche..." : "Retrouver mes billets"}
        </button>
      </form>

      {order && <TicketList order={order} />}
    </div>
  );
}
