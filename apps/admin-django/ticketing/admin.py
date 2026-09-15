from django.contrib import admin

from .models import Event, Organizer, Seat, Section, TicketType, Venue


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
