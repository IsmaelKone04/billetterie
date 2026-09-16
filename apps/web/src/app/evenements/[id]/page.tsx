import { Calendar, MapPin, Ticket, User } from "lucide-react";
import { notFound } from "next/navigation";
import { ApiError, getEvent } from "@/lib/api";
import { formatDateTime, formatFcfa } from "@/lib/format";
import PurchaseForm from "./PurchaseForm";

export default async function EventDetailPage({ params }: PageProps<"/evenements/[id]">) {
  const { id } = await params;
  const eventId = Number(id);
  if (!Number.isInteger(eventId)) notFound();

  let event;
  try {
    event = await getEvent(eventId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  return (
    <div className="grid gap-8 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <div className="flex h-40 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 via-indigo-600 to-violet-600 text-white shadow-md sm:h-52">
          <Ticket className="h-14 w-14 opacity-90" strokeWidth={1.5} />
        </div>

        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{event.title}</h1>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-600">
            <span className="flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-indigo-600" />
              {formatDateTime(event.starts_at)}
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-indigo-600" />
              {event.venue.name} — {event.venue.city}
            </span>
            <span className="flex items-center gap-1.5">
              <User className="h-4 w-4 text-indigo-600" />
              Organisé par {event.organizer_display_name}
            </span>
          </div>
        </div>

        {event.description && (
          <p className="whitespace-pre-line rounded-xl border border-slate-200 bg-white p-5 text-slate-700">
            {event.description}
          </p>
        )}

        <div>
          <h2 className="text-lg font-semibold text-slate-900">Tarifs</h2>
          <ul className="mt-3 space-y-2">
            {event.ticket_types.map((tt) => (
              <li
                key={tt.id}
                className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm"
              >
                <span className="font-medium text-slate-800">{tt.name}</span>
                <span className="font-semibold text-indigo-700">{formatFcfa(tt.price)}</span>
              </li>
            ))}
          </ul>
          {event.ticket_types.length === 0 && (
            <p className="mt-3 text-slate-600">Aucun tarif disponible pour cet événement.</p>
          )}
        </div>
      </div>

      {event.ticket_types.length > 0 && (
        <div className="lg:col-span-1">
          <div className="lg:sticky lg:top-20">
            <PurchaseForm eventId={event.id} ticketTypes={event.ticket_types} />
          </div>
        </div>
      )}
    </div>
  );
}
