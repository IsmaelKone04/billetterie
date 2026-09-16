"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { ApiError, getOrderTickets, simulatePayment, type OrderTicketsOut } from "@/lib/api";
import TicketList from "@/components/TicketList";

export default function OrderStatusPage({
  params,
  searchParams,
}: {
  params: Promise<{ transactionId: string }>;
  searchParams: Promise<{ email?: string }>;
}) {
  const { transactionId } = use(params);
  const { email = "" } = use(searchParams);

  const [order, setOrder] = useState<OrderTicketsOut | null>(null);
  const [failed, setFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [simulating, setSimulating] = useState(false);

  const refresh = useCallback(async () => {
    if (!email) {
      setError("E-mail manquant dans le lien — impossible de retrouver la commande.");
      setChecking(false);
      return;
    }
    try {
      const data = await getOrderTickets(transactionId, email);
      setOrder(data);
      setError(null);
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 409)) {
        setError(err instanceof ApiError ? err.message : "Impossible de contacter l'API.");
      }
    } finally {
      setChecking(false);
    }
  }, [transactionId, email]);

  useEffect(() => {
    // Vérification du statut de paiement au chargement de la page —
    // dépend de l'API distante, ne peut pas être calculé pendant le rendu.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  async function handleSimulate(outcome: "success" | "failed") {
    setSimulating(true);
    setError(null);
    try {
      await simulatePayment(transactionId, outcome);
      if (outcome === "failed") {
        setFailed(true);
      } else {
        await refresh();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Simulation impossible.");
    } finally {
      setSimulating(false);
    }
  }

  if (order) {
    return (
      <div className="space-y-6">
        <p className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Paiement confirmé — voici vos billets. Vous pouvez aussi les retrouver plus tard
          depuis « Mes billets » avec votre numéro de commande et votre e-mail.
        </p>
        <TicketList order={order} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-6 text-center">
      <h1 className="text-xl font-bold text-slate-900">Commande {transactionId}</h1>

      {checking && <p className="text-slate-600">Vérification du statut de paiement...</p>}

      {error && <p className="text-sm text-red-700">{error}</p>}

      {failed && (
        <div className="space-y-3 rounded-md border border-red-200 bg-red-50 p-5">
          <p className="text-sm text-red-800">Paiement refusé (simulation).</p>
          <Link href="/" className="text-sm font-medium text-indigo-700 underline">
            Retour au catalogue
          </Link>
        </div>
      )}

      {!checking && !order && !failed && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-left">
          <p className="text-sm text-slate-700">
            En attente de confirmation du paiement Mobile Money.
          </p>
          <p className="mt-2 text-sm font-medium text-amber-800">
            Démo portfolio — aucun identifiant Mobile Money réel n&apos;est configuré ici.
            Simulez l&apos;issue du paiement :
          </p>
          <div className="mt-3 flex gap-3">
            <button
              onClick={() => handleSimulate("success")}
              disabled={simulating}
              className="rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:opacity-60"
            >
              Simuler un paiement réussi
            </button>
            <button
              onClick={() => handleSimulate("failed")}
              disabled={simulating}
              className="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-60"
            >
              Simuler un échec
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
