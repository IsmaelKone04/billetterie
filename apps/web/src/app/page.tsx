import { Calendar, MapPin, PartyPopper, ShieldCheck, Smartphone, Ticket } from "lucide-react";
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
    <div className="space-y-10">
      <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-700 via-indigo-600 to-violet-600 px-6 py-10 text-white shadow-md sm:px-10 sm:py-14">
        <h1 className="max-w-xl text-3xl font-bold tracking-tight sm:text-4xl">
          Vos événements, vos billets, sans intermédiaire.
        </h1>
        <p className="mt-3 max-w-xl text-indigo-100">
          Achetez vos billets en quelques clics et payez en Mobile Money — Orange Money, MTN,
          Moov ou Wave.
        </p>
        <div className="mt-6 flex flex-wrap gap-4 text-sm text-indigo-100">
          <span className="flex items-center gap-1.5">
            <Smartphone className="h-4 w-4" /> Paiement Mobile Money
          </span>
          <span className="flex items-center gap-1.5">
            <Ticket className="h-4 w-4" /> Billets QR, places numérotées
          </span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4" /> Contrôle d&apos;accès anti-fraude
          </span>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center gap-2">
          <PartyPopper className="h-5 w-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-slate-900">Événements à venir</h2>
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        )}

        {!error && events.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
            <PartyPopper className="mx-auto h-8 w-8 text-slate-300" />
            <p className="mt-3 text-slate-600">Aucun événement publié pour le moment.</p>
          </div>
        )}

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {events.map((event) => (
            <Link
              key={event.id}
              href={`/evenements/${event.id}`}
              className="group flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-lg"
            >
              <div className="flex h-28 items-center justify-center bg-gradient-to-br from-indigo-500 to-violet-500 text-white">
                <Ticket className="h-9 w-9 opacity-90" strokeWidth={1.5} />
              </div>
              <div className="flex flex-1 flex-col gap-2 p-5">
                <h3 className="font-semibold text-slate-900 group-hover:text-indigo-700">
                  {event.title}
                </h3>
                <p className="flex items-center gap-1.5 text-sm text-slate-600">
                  <Calendar className="h-3.5 w-3.5 shrink-0" />
                  {formatDateTime(event.starts_at)}
                </p>
                <p className="flex items-center gap-1.5 text-sm text-slate-600">
                  <MapPin className="h-3.5 w-3.5 shrink-0" />
                  {event.venue.name} — {event.venue.city}
                </p>
                <p className="mt-auto pt-2 text-xs font-medium uppercase tracking-wide text-indigo-600">
                  Organisé par {event.organizer_display_name}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
