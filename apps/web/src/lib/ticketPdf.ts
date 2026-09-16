import { jsPDF } from "jspdf";
import QRCode from "qrcode";
import type { OrderTicketsOut, TicketOut } from "./api";
import { formatDateTime } from "./format";

// Génère un PDF « billet » côté client (comme le QR : jamais rendu côté
// serveur) au format paysage proche d'un vrai ticket, avec une souche
// pointillée à droite portant le QR.
export async function downloadTicketPdf(order: OrderTicketsOut, ticket: TicketOut) {
  const qrDataUrl = await QRCode.toDataURL(ticket.qr_token, { width: 300, margin: 1 });

  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: [200, 90] });

  doc.setFillColor(79, 70, 229);
  doc.rect(0, 0, 200, 90, "F");
  doc.setFillColor(255, 255, 255);
  doc.rect(3, 3, 194, 84, "F");

  doc.setDrawColor(203, 213, 225);
  doc.setLineDashPattern([2, 2], 0);
  doc.line(140, 3, 140, 87);
  doc.setLineDashPattern([], 0);

  doc.setTextColor(30, 41, 59);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(17);
  doc.text(order.event_title, 10, 17, { maxWidth: 124 });

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(71, 85, 105);
  doc.text(formatDateTime(order.event_starts_at), 10, 28);
  doc.text(`${order.venue.name} — ${order.venue.city}`, 10, 34);

  doc.setDrawColor(226, 232, 240);
  doc.line(10, 42, 132, 42);

  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.setTextColor(79, 70, 229);
  doc.text(ticket.ticket_type_name, 10, 52);

  if (ticket.seat_label) {
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(71, 85, 105);
    doc.text(`Siège ${ticket.seat_label}`, 10, 59);
  }

  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text(`Commande ${order.transaction_id}`, 10, 78);
  doc.text(`Billet #${ticket.id}`, 10, 83);

  doc.addImage(qrDataUrl, "PNG", 150, 10, 38, 38);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.setTextColor(30, 41, 59);
  doc.text("billetterie", 150, 56);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.text("Présentez ce QR à l'entrée", 150, 61, { maxWidth: 42 });
  doc.text(ticket.status === "scanne" ? "Déjà scanné" : "Valide", 150, 66);

  doc.save(`billet-${order.transaction_id}-${ticket.id}.pdf`);
}
