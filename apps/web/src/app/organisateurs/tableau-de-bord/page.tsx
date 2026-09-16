"use client";

import { BarChart3, Banknote, CalendarDays, Ticket } from "lucide-react";
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

  if (loading)
    return (
      <div className="flex items-center gap-2 text-slate-600">
        <BarChart3 className="h-5 w-5 animate-pulse text-indigo-500" />
        Chargement...
      </div>
    );
  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!dashboard) return null;

  const stats = [
    { label: "Événements", value: dashboard.total_events, icon: CalendarDays },
    { label: "Billets vendus", value: dashboard.total_tickets_sold, icon: Ticket },
    { label: "Revenu total", value: formatFcfa(dashboard.total_revenue), icon: Banknote },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Tableau de bord — {dashboard.display_name}
        </h1>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {stats.map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <Icon className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-0.5 text-2xl font-bold text-slate-900">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-slate-900">Par événement</h2>
        {dashboard.events.length === 0 ? (
          <div className="mt-3 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center">
            <CalendarDays className="mx-auto h-7 w-7 text-slate-300" />
            <p className="mt-2 text-slate-600">
              Aucun événement pour le moment (créez-en un depuis l&apos;admin Django).
            </p>
          </div>
        ) : (
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
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
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-indigo-600"
                            style={{ width: `${Math.round(event.fill_rate * 100)}%` }}
                          />
                        </div>
                        <span className="text-slate-600">{Math.round(event.fill_rate * 100)} %</span>
                      </div>
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
