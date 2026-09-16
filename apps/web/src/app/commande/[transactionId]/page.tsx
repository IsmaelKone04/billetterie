"use client";

import { CheckCircle2, Clock, Smartphone, XCircle } from "lucide-react";
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
        <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 px-5 py-4">
          <CheckCircle2 className="h-6 w-6 shrink-0 text-green-600" />
          <p className="text-sm text-green-800">
            <span className="font-semibold">Paiement confirmé</span> — voici vos billets. Vous
            pouvez aussi les retrouver plus tard depuis « Mes billets » avec votre numéro de
            commande et votre e-mail.
          </p>
        </div>
        <TicketList order={order} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="text-center">
        <h1 className="text-xl font-bold text-slate-900">Commande</h1>
        <p className="mt-1 font-mono text-sm text-slate-500">{transactionId}</p>
      </div>

      {checking && (
        <div className="flex items-center justify-center gap-2 py-6 text-slate-600">
          <Clock className="h-5 w-5 animate-pulse text-indigo-500" />
          Vérification du statut de paiement...
        </div>
      )}

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {failed && (
        <div className="space-y-3 rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <XCircle className="mx-auto h-8 w-8 text-red-600" />
          <p className="font-medium text-red-800">Paiement refusé (simulation)</p>
          <Link
            href="/"
            className="inline-block text-sm font-medium text-indigo-700 underline underline-offset-2"
          >
            Retour au catalogue
          </Link>
        </div>
      )}

      {!checking && !order && !failed && (
        <div className="overflow-hidden rounded-xl border border-indigo-200 shadow-sm">
          <div className="flex items-center gap-3 bg-indigo-50 px-5 py-4">
            <Smartphone className="h-6 w-6 shrink-0 text-indigo-600" />
            <p className="text-sm text-indigo-900">
              En attente de confirmation du paiement <strong>Mobile Money</strong>.
            </p>
          </div>
          <div className="space-y-3 bg-white px-5 py-4">
            <p className="rounded-md bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
              Démo portfolio — aucun identifiant Mobile Money réel n&apos;est configuré ici.
              Simulez vous-même l&apos;issue du paiement ci-dessous :
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => handleSimulate("success")}
                disabled={simulating}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-md bg-green-600 px-3 py-2.5 text-sm font-medium text-white transition hover:bg-green-500 disabled:opacity-60"
              >
                <CheckCircle2 className="h-4 w-4" />
                Paiement réussi
              </button>
              <button
                onClick={() => handleSimulate("failed")}
                disabled={simulating}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-red-300 px-3 py-2.5 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:opacity-60"
              >
                <XCircle className="h-4 w-4" />
                Échec
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
