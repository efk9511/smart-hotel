from django.urls import path
from . import views

app_name = "hotel"

urlpatterns = [
    # Public
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("room-types/", views.room_type_list, name="room_type_list"),
    path("room-types/<int:pk>/", views.room_type_detail, name="room_type_detail"),
    path("offers/", views.offers_list, name="offers_list"),
    path("reserve/", views.start_reservation, name="start_reservation"),
    path("reserve/confirm/", views.confirm_reservation, name="confirm_reservation"),
    path("reservation/<int:pk>/print/", views.print_reservation, name="print_reservation"),

    # Auth
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),

    # Theme
    path("toggle-theme/", views.toggle_theme, name="toggle_theme"),

    # Guest
    path("guest/dashboard/", views.guest_dashboard, name="guest_dashboard"),
    path("guest/profile/", views.guest_profile, name="guest_profile"),
    path("guest/reservations/", views.my_room_reservations, name="my_room_reservations"),
    path("guest/reservations/<int:pk>/", views.my_room_reservation_detail, name="my_room_reservation_detail"),
    path("guest/reservations/<int:pk>/cancel/", views.cancel_reservation, name="cancel_reservation"),
    path("guest/common-reservations/", views.my_common_reservations, name="my_common_reservations"),
    path("guest/common-reservations/create/", views.create_common_reservation, name="create_common_reservation"),
    path("guest/tickets/", views.my_tickets, name="my_tickets"),
    path("guest/tickets/create/", views.create_ticket, name="create_ticket"),
    path("guest/tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),

    # Staff
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/tickets/", views.staff_tickets, name="staff_tickets"),
    path("staff/tickets/<int:pk>/", views.staff_ticket_detail, name="staff_ticket_detail"),
    path("staff/tickets/<int:pk>/status/", views.staff_update_ticket_status, name="staff_update_ticket_status"),
    path("staff/tickets/<int:pk>/note/", views.staff_add_note, name="staff_add_note"),

    # Manager
    path("manager/dashboard/", views.manager_dashboard, name="manager_dashboard"),
    path("manager/users/", views.manager_users, name="manager_users"),
    path("manager/users/create/", views.manager_user_create, name="manager_user_create"),
    path("manager/users/<int:pk>/edit/", views.manager_user_edit, name="manager_user_edit"),
    path("manager/users/<int:pk>/delete/", views.manager_user_delete, name="manager_user_delete"),
    path("manager/room-types/", views.manager_room_types, name="manager_room_types"),
    path("manager/room-types/create/", views.manager_room_type_create, name="manager_room_type_create"),
    path("manager/room-types/<int:pk>/edit/", views.manager_room_type_edit, name="manager_room_type_edit"),
    path("manager/room-types/<int:pk>/delete/", views.manager_room_type_delete, name="manager_room_type_delete"),
    path("manager/rooms/", views.manager_rooms, name="manager_rooms"),
    path("manager/rooms/create/", views.manager_room_create, name="manager_room_create"),
    path("manager/rooms/<int:pk>/edit/", views.manager_room_edit, name="manager_room_edit"),
    path("manager/rooms/<int:pk>/delete/", views.manager_room_delete, name="manager_room_delete"),
    path("manager/rooms/<int:pk>/status/", views.manager_room_change_status, name="manager_room_change_status"),
    path("manager/announcements/", views.manager_announcements, name="manager_announcements"),
    path("manager/announcements/create/", views.manager_announcement_create, name="manager_announcement_create"),
    path("manager/announcements/<int:pk>/edit/", views.manager_announcement_edit, name="manager_announcement_edit"),
    path("manager/announcements/<int:pk>/delete/", views.manager_announcement_delete, name="manager_announcement_delete"),
    path("manager/reservations/", views.manager_reservations, name="manager_reservations"),
    path("manager/reservations/<int:pk>/", views.manager_reservation_detail, name="manager_reservation_detail"),
    path("manager/reservations/<int:pk>/status/", views.manager_update_reservation_status, name="manager_update_reservation_status"),
    path("manager/reservations/<int:pk>/assign-room/", views.manager_assign_room, name="manager_assign_room"),
    path("manager/common-reservations/", views.manager_common_reservations, name="manager_common_reservations"),
    path("manager/tickets/", views.manager_tickets, name="manager_tickets"),
    path("manager/tickets/<int:pk>/", views.manager_ticket_detail, name="manager_ticket_detail"),
    path("manager/tickets/<int:pk>/assign/", views.manager_assign_ticket, name="manager_assign_ticket"),
    path("manager/tickets/<int:pk>/status/", views.manager_update_ticket_status, name="manager_update_ticket_status"),
    path("manager/reports/", views.manager_reports, name="manager_reports"),
    path("manager/offers/", views.manager_offers, name="manager_offers"),
    path("manager/offers/create/", views.manager_offer_create, name="manager_offer_create"),
    path("manager/offers/<int:pk>/edit/", views.manager_offer_edit, name="manager_offer_edit"),
    path("manager/offers/<int:pk>/delete/", views.manager_offer_delete, name="manager_offer_delete"),

    # API
    path("api/room-types/", views.api_room_types, name="api_room_types"),
    path("api/common-areas/", views.api_common_areas, name="api_common_areas"),
    path("rooms/<int:pk>/availability/", views.room_type_availability_api, name="room_type_availability_api"),
]
