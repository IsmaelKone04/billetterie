from django.contrib import admin

from .models import (
    Event,
    Order,
    Organizer,
    PaymentEvent,
    Seat,
    Section,
    Ticket,
    TicketType,
    Venue,
)


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "phone", "created_at")
    search_fields = ("display_name", "user__username", "phone")


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city")
    search_fields = ("name", "city")


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("venue", "name", "has_numbered_seats", "capacity")
    list_filter = ("venue", "has_numbered_seats")
    inlines = [SeatInline]


class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "venue", "starts_at", "status")
    list_filter = ("status", "venue")
    search_fields = ("title", "organizer__display_name")
    inlines = [TicketTypeInline]


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ("event", "name", "price", "quota", "section")
    list_filter = ("event",)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ("qr_secret", "scanned_at", "scanned_by")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "event",
        "buyer_email",
        "amount_total",
        "status",
        "payment_provider",
        "created_at",
    )
    list_filter = ("status", "payment_provider", "event")
    search_fields = ("transaction_id", "buyer_email", "buyer_phone")
    readonly_fields = ("transaction_id", "created_at", "updated_at")
    inlines = [TicketInline]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "ticket_type", "seat", "status", "scanned_at")
    list_filter = ("status", "ticket_type__event")
    search_fields = ("qr_secret", "order__transaction_id", "order__buyer_email")
    readonly_fields = ("qr_secret",)


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    """Journal d'audit — lecture seule, jamais modifié à la main."""

    list_display = (
        "provider",
        "provider_event_id",
        "order",
        "outcome",
        "signature_valid",
        "received_at",
    )
    list_filter = ("provider", "outcome", "signature_valid")
    search_fields = ("provider_event_id", "order__transaction_id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
