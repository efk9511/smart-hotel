from django.contrib import admin
from .models import (
    User, RoomType, Room, RoomReservation,
    CommonArea, CommonAreaReservation, Announcement,
    Ticket, TicketNote
)

admin.site.register(User)
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(RoomReservation)
admin.site.register(CommonArea)
admin.site.register(CommonAreaReservation)
admin.site.register(Announcement)
admin.site.register(Ticket)
admin.site.register(TicketNote)
