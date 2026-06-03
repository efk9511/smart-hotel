from .models import Announcement, RoomReservation, Ticket


def theme_context(request):
    theme = request.session.get("theme") or request.COOKIES.get("theme", "light")
    return {
        "theme": theme,
        "announcements_count": Announcement.objects.filter(is_active=True).count(),
        "open_tickets_count": Ticket.objects.filter(status__in=["open", "assigned", "in_progress"]).count(),
        "active_reservations_count": RoomReservation.objects.filter(status__in=["pending", "confirmed"]).count(),
    }
