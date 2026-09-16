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
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{event.title}</h1>
        <p className="mt-1 text-slate-600">{formatDateTime(event.starts_at)}</p>
        <p className="mt-1 text-slate-600">
          {event.venue.name} — {event.venue.city}
        </p>
        <p className="mt-3 text-xs font-medium uppercase tracking-wide text-indigo-600">
          Organisé par {event.organizer_display_name}
        </p>
      </div>

      {event.description && (
        <p className="whitespace-pre-line text-slate-700">{event.description}</p>
      )}

      <div>
        <h2 className="text-lg font-semibold text-slate-900">Tarifs</h2>
        <ul className="mt-3 space-y-2">
          {event.ticket_types.map((tt) => (
            <li
              key={tt.id}
              className="flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-3"
            >
              <span className="font-medium text-slate-800">{tt.name}</span>
              <span className="text-slate-600">{formatFcfa(tt.price)}</span>
            </li>
          ))}
        </ul>
        {event.ticket_types.length === 0 && (
          <p className="mt-3 text-slate-600">Aucun tarif disponible pour cet événement.</p>
        )}
      </div>

      {event.ticket_types.length > 0 && (
        <PurchaseForm eventId={event.id} ticketTypes={event.ticket_types} />
      )}
    </div>
  );
}
