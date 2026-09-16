import Link from "next/link";
import { ApiError, getEvents, type EventListItem } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

export default async function CataloguePage() {
  let events: EventListItem[];
  let error: string | null = null;
  try {
    events = await getEvents();
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Impossible de contacter l'API.";
    events = [];
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Événements à venir</h1>
        <p className="mt-1 text-slate-600">
          Découvrez les événements publiés et achetez vos billets en ligne, paiement Mobile
          Money accepté.
        </p>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!error && events.length === 0 && (
        <p className="text-slate-600">Aucun événement publié pour le moment.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {events.map((event) => (
          <Link
            key={event.id}
            href={`/evenements/${event.id}`}
            className="block rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
          >
            <h2 className="text-lg font-semibold text-slate-900">{event.title}</h2>
            <p className="mt-1 text-sm text-slate-600">{formatDateTime(event.starts_at)}</p>
            <p className="mt-1 text-sm text-slate-600">
              {event.venue.name} — {event.venue.city}
            </p>
            <p className="mt-3 text-xs font-medium uppercase tracking-wide text-indigo-600">
              Organisé par {event.organizer_display_name}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
