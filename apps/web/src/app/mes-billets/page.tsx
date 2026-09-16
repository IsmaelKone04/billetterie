"use client";

import { Search, Ticket } from "lucide-react";
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
      <div className="text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <Ticket className="h-6 w-6" />
        </span>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">Mes billets</h1>
        <p className="mt-1 text-slate-600">
          Retrouvez vos billets avec le numéro de commande et l&apos;e-mail utilisés à l&apos;achat.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <label className="block text-sm">
          <span className="text-slate-700">Numéro de commande</span>
          <input
            required
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="vous@example.com"
          />
        </label>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-1.5 rounded-md bg-gradient-to-br from-indigo-600 to-violet-600 px-4 py-2.5 font-medium text-white shadow-sm transition hover:brightness-110 disabled:opacity-60"
        >
          <Search className="h-4 w-4" />
          {loading ? "Recherche..." : "Retrouver mes billets"}
        </button>
      </form>

      {order && <TicketList order={order} />}
    </div>
  );
}
