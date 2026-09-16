"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, organizerDashboard, type OrganizerDashboardOut } from "@/lib/api";
import { clearToken, getStoredToken } from "@/lib/auth";
import { formatFcfa } from "@/lib/format";

export default function OrganizerDashboardPage() {
  const router = useRouter();
  const [dashboard, setDashboard] = useState<OrganizerDashboardOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.replace("/organisateurs/connexion");
      return;
    }
    organizerDashboard(token)
      .then(setDashboard)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
          router.replace("/organisateurs/connexion");
          return;
        }
        setError(err instanceof ApiError ? err.message : "Impossible de charger le tableau de bord.");
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) return <p className="text-slate-600">Chargement...</p>;
  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!dashboard) return null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Tableau de bord — {dashboard.display_name}
        </h1>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Événements</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{dashboard.total_events}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Billets vendus</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{dashboard.total_tickets_sold}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">Revenu total</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            {formatFcfa(dashboard.total_revenue)}
          </p>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-slate-900">Par événement</h2>
        {dashboard.events.length === 0 ? (
          <p className="mt-2 text-slate-600">
            Aucun événement pour le moment (créez-en un depuis l&apos;admin Django).
          </p>
        ) : (
          <div className="mt-3 overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Événement</th>
                  <th className="px-4 py-3 font-medium">Statut</th>
                  <th className="px-4 py-3 font-medium">Billets vendus</th>
                  <th className="px-4 py-3 font-medium">Remplissage</th>
                  <th className="px-4 py-3 font-medium">Revenu</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.events.map((event) => (
                  <tr key={event.event_id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">
                      <Link
                        href={`/evenements/${event.event_id}`}
                        className="font-medium text-indigo-700 hover:underline"
                      >
                        {event.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{event.status}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {event.tickets_sold} / {event.quota_total}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {Math.round(event.fill_rate * 100)} %
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatFcfa(event.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
