import json
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers

from .decorators import guest_required, manager_required, staff_required
from .forms import (
    AnnouncementForm, CommonAreaReservationForm, HotelOfferForm, RoomAssignForm,
    RoomForm, RoomReservationForm, RoomTypeForm, TicketAssignForm, TicketForm,
    TicketNoteForm, TicketStatusForm, UserCreateForm, UserProfileForm,
    UserRegistrationForm, UserUpdateForm,
)
from .models import (
    Announcement, CommonArea, CommonAreaReservation, HotelOffer, Room,
    RoomReservation, RoomType, Ticket, TicketNote, User,
)

# ─── Serializers ───────────────────────────────────────────────────────────────

class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = "__all__"


class CommonAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonArea
        fields = "__all__"


# ─── API Views ─────────────────────────────────────────────────────────────────

@api_view(["GET"])
def api_room_types(request):
    room_types = RoomType.objects.filter(is_active=True)
    serializer = RoomTypeSerializer(room_types, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def api_common_areas(request):
    areas = CommonArea.objects.filter(is_active=True)
    serializer = CommonAreaSerializer(areas, many=True)
    return Response(serializer.data)


def room_type_availability_api(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk, is_active=True)
    check_in = request.GET.get("check_in")
    check_out = request.GET.get("check_out")

    if not check_in or not check_out:
        return JsonResponse({"error": "check_in and check_out are required"}, status=400)

    try:
        ci = date.fromisoformat(check_in)
        co = date.fromisoformat(check_out)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid date format"}, status=400)

    if co <= ci:
        return JsonResponse({"error": "check_out must be after check_in"}, status=400)

    available_count = room_type.get_available_rooms(ci, co).count()
    total_rooms = room_type.rooms.filter(is_active=True).count()
    unavailable_count = total_rooms - available_count
    is_available = available_count > 0

    return JsonResponse({
        "available_count": available_count,
        "total_rooms": total_rooms,
        "unavailable_count": unavailable_count,
        "is_available": is_available,
        "message": "" if is_available else "No rooms of this type are available for the selected dates.",
    })


# ─── Theme ─────────────────────────────────────────────────────────────────────

def toggle_theme(request):
    theme = request.GET.get("theme", "light")
    request.session["theme"] = theme
    response = redirect(request.META.get("HTTP_REFERER", "hotel:home"))
    response.set_cookie("theme", theme, max_age=365 * 24 * 3600)
    return response


# ─── Auth Views ────────────────────────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect("hotel:home")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to Seaside Hotel.")
            next_url = request.session.pop("reservation_next", None)
            return redirect(next_url or "hotel:guest_dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "hotel/auth/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("hotel:home")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.session.pop("reservation_next", None)
            if next_url:
                return redirect(next_url)
            if user.role == "manager":
                return redirect("hotel:manager_dashboard")
            elif user.role == "staff":
                return redirect("hotel:staff_dashboard")
            else:
                return redirect("hotel:guest_dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "hotel/auth/login.html")


def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("hotel:home")


# ─── Public Views ──────────────────────────────────────────────────────────────

def home(request):
    room_types = RoomType.objects.filter(is_active=True)[:6]
    announcements = Announcement.objects.filter(is_active=True, target_audience__in=["all", "guests"])[:3]
    return render(request, "hotel/public/home.html", {
        "room_types": room_types,
        "announcements": announcements,
    })


def about(request):
    return render(request, "hotel/public/about.html")


def room_type_list(request):
    room_types = RoomType.objects.filter(is_active=True)
    return render(request, "hotel/public/room_type_list.html", {"room_types": room_types})


def room_type_detail(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk, is_active=True)
    available = room_type.available_rooms_count()
    unavailable_ranges = room_type.get_unavailable_date_ranges()
    total_rooms = room_type.rooms.filter(is_active=True).count()
    return render(request, "hotel/public/room_type_detail.html", {
        "room_type": room_type,
        "available_rooms": available,
        "total_rooms": total_rooms,
        "unavailable_ranges": unavailable_ranges,
    })


def start_reservation(request):
    room_types = RoomType.objects.filter(is_active=True)
    selected_type = None
    check_in = request.GET.get("check_in")
    check_out = request.GET.get("check_out")
    room_type_id = request.GET.get("room_type")

    if room_type_id:
        selected_type = get_object_or_404(RoomType, pk=room_type_id, is_active=True)

    if request.method == "POST":
        room_type_id = request.POST.get("room_type")
        check_in = request.POST.get("check_in")
        check_out = request.POST.get("check_out")
        guests = request.POST.get("guests", 1)

        if not all([room_type_id, check_in, check_out]):
            messages.error(request, "Please fill in all fields.")
            return redirect("hotel:start_reservation")

        rt = get_object_or_404(RoomType, pk=int(room_type_id), is_active=True)
        ci = date.fromisoformat(check_in)
        co = date.fromisoformat(check_out)
        if ci < timezone.now().date():
            messages.error(request, "Check-in date cannot be in the past.")
            return redirect("hotel:start_reservation")
        if co <= ci:
            messages.error(request, "Check-out date must be after check-in date.")
            return redirect("hotel:start_reservation")
        if int(guests) > rt.capacity:
            messages.error(request, f"Maximum capacity for {rt.name} is {rt.capacity} guests.")
            return redirect("hotel:start_reservation")
        if rt.get_available_rooms(ci, co).count() == 0:
            messages.error(request, "No rooms of this type are available for the selected dates. Please choose another room type or different dates.")
            return redirect("hotel:start_reservation")

        request.session["reservation_data"] = {
            "room_type_id": int(room_type_id),
            "check_in": check_in,
            "check_out": check_out,
            "guests": int(guests),
        }

        if not request.user.is_authenticated:
            request.session["reservation_next"] = "hotel:confirm_reservation"
            messages.info(request, "Please log in or create an account to complete your reservation.")
            return redirect("hotel:login")

        return redirect("hotel:confirm_reservation")

    # Build availability info per room type if dates are provided
    room_type_availability = {}
    if check_in and check_out:
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
            if co > ci and ci >= timezone.now().date():
                for rt in room_types:
                    available = rt.get_available_rooms(ci, co).count()
                    total = rt.rooms.filter(is_active=True).count()
                    room_type_availability[rt.id] = {
                        "available": available,
                        "total": total,
                        "unavailable": total - available,
                        "capacity": rt.capacity,
                    }
        except (ValueError, TypeError):
            pass

    unavailable_ranges = []
    selected_total_rooms = 0
    selected_avail_rooms = 0
    if selected_type:
        unavailable_ranges = selected_type.get_unavailable_date_ranges()
        selected_total_rooms = selected_type.rooms.filter(is_active=True).count()
        selected_avail_rooms = selected_type.available_rooms_count()

    return render(request, "hotel/public/start_reservation.html", {
        "room_types": room_types,
        "selected_type": selected_type,
        "check_in": check_in,
        "check_out": check_out,
        "today": timezone.now().date(),
        "room_type_availability": room_type_availability,
        "unavailable_ranges": unavailable_ranges,
        "selected_total_rooms": selected_total_rooms,
        "selected_avail_rooms": selected_avail_rooms,
    })


def confirm_reservation(request):
    if not request.user.is_authenticated:
        request.session["reservation_next"] = "hotel:confirm_reservation"
        messages.info(request, "Please log in or create an account to complete your reservation.")
        return redirect("hotel:login")

    data = request.session.get("reservation_data")
    if not data:
        messages.error(request, "No reservation data found. Please start again.")
        return redirect("hotel:start_reservation")

    room_type = get_object_or_404(RoomType, pk=data["room_type_id"])
    check_in = date.fromisoformat(data["check_in"])
    check_out = date.fromisoformat(data["check_out"])
    nights = (check_out - check_in).days
    total_price = room_type.price_per_night * nights
    available_rooms = room_type.get_available_rooms(check_in, check_out)
    available_count = available_rooms.count()

    if request.method == "POST":
        if available_count == 0:
            messages.error(request, "Sorry, this room type is no longer available for the selected dates. Please choose another date or room type.")
            del request.session["reservation_data"]
            return redirect("hotel:start_reservation")

        room = available_rooms.first()
        reservation = RoomReservation.objects.create(
            guest=request.user,
            room_type=room_type,
            room=room,
            check_in=check_in,
            check_out=check_out,
            number_of_guests=data["guests"],
            status="confirmed",
            total_price=total_price,
        )
        del request.session["reservation_data"]
        messages.success(request, "Reservation confirmed! Thank you for booking with Seaside Hotel.")
        return redirect("hotel:my_room_reservation_detail", pk=reservation.pk)

    total_rooms = room_type.rooms.filter(is_active=True).count()

    return render(request, "hotel/public/confirm_reservation.html", {
        "room_type": room_type,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "guests": data["guests"],
        "total_price": total_price,
        "available_rooms_count": available_count,
        "total_rooms": total_rooms,
    })


@login_required
def print_reservation(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk, guest=request.user)
    return render(request, "hotel/public/print_reservation.html", {"reservation": reservation})


# ─── Guest Views ───────────────────────────────────────────────────────────────

@guest_required
def guest_dashboard(request):
    user = request.user
    active_reservations = RoomReservation.objects.filter(
        guest=user, status__in=["pending", "confirmed"]
    ).select_related("room_type", "room")[:5]
    recent_tickets = Ticket.objects.filter(guest=user).order_by("-created_at")[:5]
    common_reservations = CommonAreaReservation.objects.filter(
        guest=user, status__in=["pending", "confirmed"]
    ).select_related("common_area")[:5]

    today = timezone.now().date()
    cancelable_ids = set()
    for res in active_reservations:
        if res.status in ("pending", "confirmed") and (res.check_in - today).days >= 7:
            cancelable_ids.add(res.id)

    context = {
        "active_reservations": active_reservations,
        "recent_tickets": recent_tickets,
        "common_reservations": common_reservations,
        "reservation_count": RoomReservation.objects.filter(guest=user).count(),
        "ticket_count": Ticket.objects.filter(guest=user).count(),
        "open_ticket_count": Ticket.objects.filter(guest=user, status__in=["open", "assigned", "in_progress"]).count(),
        "cancelable_ids": cancelable_ids,
    }
    return render(request, "hotel/guest/dashboard.html", context)


@guest_required
def guest_profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("hotel:guest_profile")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "hotel/guest/profile.html", {"form": form})


@guest_required
def my_room_reservations(request):
    qs = RoomReservation.objects.filter(guest=request.user).select_related("room_type", "room").order_by("-created_at")
    paginator = Paginator(qs, 10)
    page = request.GET.get("page")
    reservations = paginator.get_page(page)
    today = timezone.now().date()
    cancelable_ids = set()
    for res in reservations:
        if res.status in ("pending", "confirmed") and (res.check_in - today).days >= 7:
            cancelable_ids.add(res.id)
    return render(request, "hotel/guest/room_reservations.html", {
        "reservations": reservations,
        "cancelable_ids": cancelable_ids,
    })


@guest_required
def my_room_reservation_detail(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk, guest=request.user)
    days_until_checkin = (reservation.check_in - timezone.now().date()).days
    can_cancel = reservation.status in ("pending", "confirmed") and days_until_checkin >= 7
    return render(request, "hotel/guest/room_reservation_detail.html", {
        "reservation": reservation,
        "can_cancel": can_cancel,
        "days_until_checkin": days_until_checkin,
    })


@guest_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk, guest=request.user)
    if reservation.status not in ("pending", "confirmed"):
        messages.error(request, "This reservation cannot be cancelled.")
        return redirect("hotel:my_room_reservation_detail", pk=reservation.pk)
    days_until_checkin = (reservation.check_in - timezone.now().date()).days
    if days_until_checkin < 7:
        messages.error(
            request,
            f"Cancellation is only allowed at least 7 days before check-in. "
            f"Your check-in is in {days_until_checkin} day(s)."
        )
        return redirect("hotel:my_room_reservation_detail", pk=reservation.pk)
    if request.method == "POST":
        reservation.status = "cancelled"
        if reservation.room:
            reservation.room.status = "available"
            reservation.room.save()
        reservation.save()
        messages.success(request, f"Reservation #{reservation.id} has been cancelled.")
        return redirect("hotel:my_room_reservations")
    return redirect("hotel:my_room_reservation_detail", pk=reservation.pk)


@guest_required
def my_common_reservations(request):
    reservations = CommonAreaReservation.objects.filter(guest=request.user).select_related("common_area").order_by("-created_at")
    return render(request, "hotel/guest/common_reservations.html", {"reservations": reservations})


@guest_required
def create_common_reservation(request):
    if request.method == "POST":
        form = CommonAreaReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.guest = request.user
            reservation.save()
            messages.success(request, "Common area reservation created successfully!")
            return redirect("hotel:my_common_reservations")
    else:
        form = CommonAreaReservationForm()
    return render(request, "hotel/guest/create_common_reservation.html", {"form": form})


@guest_required
def my_tickets(request):
    tickets = Ticket.objects.filter(guest=request.user).order_by("-created_at")
    return render(request, "hotel/guest/tickets.html", {"tickets": tickets})


@guest_required
def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.guest = request.user
            ticket.save()
            messages.success(request, "Ticket created successfully. We will get back to you soon.")
            return redirect("hotel:my_tickets")
    else:
        form = TicketForm()
    return render(request, "hotel/guest/create_ticket.html", {"form": form})


@guest_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, guest=request.user)
    notes = ticket.notes.select_related("user").all()
    return render(request, "hotel/guest/ticket_detail.html", {"ticket": ticket, "notes": notes})


# ─── Staff Views ───────────────────────────────────────────────────────────────

@staff_required
def staff_dashboard(request):
    staff = request.user
    assigned_tickets = Ticket.objects.filter(assigned_staff=staff).select_related("guest", "room").order_by("-created_at")

    # Derive room info for tickets without an explicit room
    guest_ids = {t.guest_id for t in assigned_tickets if not t.room_id}
    if guest_ids:
        active_reservations = RoomReservation.objects.filter(
            guest_id__in=guest_ids,
            status="confirmed",
            room__isnull=False,
        ).select_related("room").order_by("-created_at")
        guest_room_map = {}
        for res in active_reservations:
            if res.guest_id not in guest_room_map:
                guest_room_map[res.guest_id] = res.room.room_number
        for t in assigned_tickets:
            if not t.room_id and t.guest_id in guest_room_map:
                t.guest_room_display = guest_room_map[t.guest_id]

    context = {
        "assigned_tickets": assigned_tickets,
        "total_assigned": assigned_tickets.count(),
        "in_progress": assigned_tickets.filter(status="in_progress").count(),
        "resolved": assigned_tickets.filter(status="resolved").count(),
        "open_count": assigned_tickets.filter(status="open").count(),
    }
    return render(request, "hotel/staff/dashboard.html", context)


@staff_required
def staff_tickets(request):
    tickets = Ticket.objects.filter(assigned_staff=request.user).select_related("guest", "room").order_by("-updated_at")

    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    search_query = request.GET.get("q")

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    paginator = Paginator(tickets, 10)
    page = request.GET.get("page")
    tickets = paginator.get_page(page)

    # Derive room info for tickets without an explicit room
    guest_ids = {t.guest_id for t in tickets if not t.room_id}
    if guest_ids:
        active_reservations = RoomReservation.objects.filter(
            guest_id__in=guest_ids,
            status="confirmed",
            room__isnull=False,
        ).select_related("room").order_by("-created_at")
        guest_room_map = {}
        for res in active_reservations:
            if res.guest_id not in guest_room_map:
                guest_room_map[res.guest_id] = res.room.room_number
        for t in tickets:
            if not t.room_id and t.guest_id in guest_room_map:
                t.guest_room_display = guest_room_map[t.guest_id]

    return render(request, "hotel/staff/tickets.html", {
        "tickets": tickets,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "search_query": search_query,
    })


@staff_required
def staff_ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, assigned_staff=request.user)
    notes = ticket.notes.select_related("user").all()
    note_form = TicketNoteForm()
    status_form = TicketStatusForm(instance=ticket)

    # If ticket has no room, try guest's current confirmed reservation
    guest_room = None
    if not ticket.room:
        active_res = RoomReservation.objects.filter(
            guest=ticket.guest,
            status="confirmed",
            room__isnull=False,
        ).select_related("room").first()
        if active_res:
            guest_room = active_res.room

    return render(request, "hotel/staff/ticket_detail.html", {
        "ticket": ticket,
        "notes": notes,
        "note_form": note_form,
        "status_form": status_form,
        "guest_room": guest_room,
    })


@staff_required
def staff_update_ticket_status(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, assigned_staff=request.user)
    if request.method == "POST":
        form = TicketStatusForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True, "status": ticket.get_status_display()})
            messages.success(request, "Ticket status updated.")
            return redirect("hotel:staff_ticket_detail", pk=ticket.pk)
    return redirect("hotel:staff_ticket_detail", pk=ticket.pk)


@staff_required
def staff_add_note(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, assigned_staff=request.user)
    if request.method == "POST":
        form = TicketNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.ticket = ticket
            note.user = request.user
            note.save()
            messages.success(request, "Note added.")
    return redirect("hotel:staff_ticket_detail", pk=ticket.pk)


# ─── Manager Views ─────────────────────────────────────────────────────────────

@manager_required
def manager_dashboard(request):
    total_guests = User.objects.filter(role="guest").count()
    total_staff = User.objects.filter(role="staff").count()
    total_rooms = Room.objects.filter(is_active=True).count()
    available_rooms = Room.objects.filter(status="available", is_active=True).count()
    active_reservations = RoomReservation.objects.filter(status__in=["pending", "confirmed"]).count()
    open_tickets = Ticket.objects.filter(status__in=["open", "assigned", "in_progress"]).count()
    resolved_tickets = Ticket.objects.filter(status="resolved").count()
    total_revenue = RoomReservation.objects.filter(status="confirmed").aggregate(Sum("total_price"))["total_price__sum"] or 0
    recent_reservations = RoomReservation.objects.select_related("guest", "room_type").order_by("-created_at")[:5]
    recent_tickets = Ticket.objects.select_related("guest").order_by("-created_at")[:5]

    context = {
        "total_guests": total_guests,
        "total_staff": total_staff,
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "active_reservations": active_reservations,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "total_revenue": total_revenue,
        "recent_reservations": recent_reservations,
        "recent_tickets": recent_tickets,
    }
    return render(request, "hotel/manager/dashboard.html", context)


@manager_required
def manager_users(request):
    role_filter = request.GET.get("role")
    search_query = request.GET.get("q")
    users = User.objects.all().order_by("-date_joined")

    if role_filter:
        users = users.filter(role=role_filter)
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    paginator = Paginator(users, 15)
    page = request.GET.get("page")
    users = paginator.get_page(page)

    return render(request, "hotel/manager/users.html", {
        "users": users,
        "role_filter": role_filter,
        "search_query": search_query,
    })


@manager_required
def manager_user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("hotel:manager_users")
    else:
        form = UserCreateForm()
    return render(request, "hotel/manager/user_form.html", {"form": form, "title": "Create User"})


@manager_required
def manager_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("hotel:manager_users")
    else:
        form = UserUpdateForm(instance=user)
    return render(request, "hotel/manager/user_form.html", {"form": form, "title": "Edit User", "edit_user": user})


@manager_required
def manager_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted.")
        return redirect("hotel:manager_users")
    return render(request, "hotel/manager/user_confirm_delete.html", {"delete_user": user})


@manager_required
def manager_room_types(request):
    room_types = RoomType.objects.all().order_by("-created_at")
    return render(request, "hotel/manager/room_types.html", {"room_types": room_types})


@manager_required
def manager_room_type_create(request):
    if request.method == "POST":
        form = RoomTypeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Room type created.")
            return redirect("hotel:manager_room_types")
    else:
        form = RoomTypeForm()
    return render(request, "hotel/manager/room_type_form.html", {"form": form, "title": "Create Room Type"})


@manager_required
def manager_room_type_edit(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk)
    if request.method == "POST":
        form = RoomTypeForm(request.POST, request.FILES, instance=room_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Room type updated.")
            return redirect("hotel:manager_room_types")
    else:
        form = RoomTypeForm(instance=room_type)
    return render(request, "hotel/manager/room_type_form.html", {"form": form, "title": "Edit Room Type"})


@manager_required
def manager_room_type_delete(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk)
    if request.method == "POST":
        room_type.delete()
        messages.success(request, "Room type deleted.")
        return redirect("hotel:manager_room_types")
    return render(request, "hotel/manager/room_type_confirm_delete.html", {"room_type": room_type})


@manager_required
def manager_rooms(request):
    today = timezone.now().date()
    room_types = RoomType.objects.filter(is_active=True).prefetch_related(
        Prefetch("rooms", queryset=Room.objects.all().order_by("room_number"))
    )

    # Gather all room IDs for one-shot reservation query
    all_room_ids = []
    for rt in room_types:
        all_room_ids.extend(rt.rooms.values_list("id", flat=True))

    active_reservations = RoomReservation.objects.filter(
        room_id__in=all_room_ids,
        status__in=["pending", "confirmed"],
        check_in__lte=today,
        check_out__gt=today,
    ).select_related("guest")

    active_res_map = {}
    for ar in active_reservations:
        if ar.room_id not in active_res_map:
            active_res_map[ar.room_id] = ar

    type_data = []
    for rt in room_types:
        rooms = list(rt.rooms.all().order_by("room_number"))
        counts = {"available": 0, "occupied": 0, "maintenance": 0, "inactive": 0}
        for room in rooms:
            status_key = room.status if room.status in counts else "available"
            counts[status_key] += 1
        type_data.append({
            "room_type": rt,
            "rooms": rooms,
            "counts": counts,
            "total": len(rooms),
        })

    return render(request, "hotel/manager/grouped_rooms.html", {
        "type_data": type_data,
        "active_res_map": active_res_map,
        "today": today,
    })


@manager_required
def manager_room_change_status(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = ["available", "occupied", "maintenance", "inactive"]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status.")
            return redirect("hotel:manager_rooms")

        today = timezone.now().date()
        has_active = RoomReservation.objects.filter(
            room=room,
            status__in=["pending", "confirmed"],
            check_in__lte=today,
            check_out__gt=today,
        ).exists()

        if new_status == "available" and has_active:
            messages.error(
                request,
                f"Cannot set Room {room.room_number} to Available — it has an active reservation.",
            )
            return redirect("hotel:manager_rooms")

        room.status = new_status
        room.save()
        messages.success(request, f"Room {room.room_number} status changed to {room.get_status_display()}.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            from django.http import JsonResponse
            return JsonResponse({"success": True, "status": new_status, "label": room.get_status_display()})

        return redirect("hotel:manager_rooms")

    return redirect("hotel:manager_rooms")


@manager_required
def manager_room_create(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Room created.")
            return redirect("hotel:manager_rooms")
    else:
        form = RoomForm()
    return render(request, "hotel/manager/room_form.html", {"form": form, "title": "Create Room"})


@manager_required
def manager_room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Room updated.")
            return redirect("hotel:manager_rooms")
    else:
        form = RoomForm(instance=room)
    return render(request, "hotel/manager/room_form.html", {"form": form, "title": "Edit Room"})


@manager_required
def manager_room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == "POST":
        room.delete()
        messages.success(request, "Room deleted.")
        return redirect("hotel:manager_rooms")
    return render(request, "hotel/manager/room_confirm_delete.html", {"room": room})


@manager_required
def manager_announcements(request):
    announcements = Announcement.objects.select_related("created_by").all().order_by("-created_at")
    return render(request, "hotel/manager/announcements.html", {"announcements": announcements})


@manager_required
def manager_announcement_create(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            messages.success(request, "Announcement created.")
            return redirect("hotel:manager_announcements")
    else:
        form = AnnouncementForm()
    return render(request, "hotel/manager/announcement_form.html", {"form": form, "title": "Create Announcement"})


@manager_required
def manager_announcement_edit(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=ann)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated.")
            return redirect("hotel:manager_announcements")
    else:
        form = AnnouncementForm(instance=ann)
    return render(request, "hotel/manager/announcement_form.html", {"form": form, "title": "Edit Announcement"})


@manager_required
def manager_announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Announcement deleted.")
        return redirect("hotel:manager_announcements")
    return render(request, "hotel/manager/announcement_confirm_delete.html", {"announcement": ann})


@manager_required
def manager_reservations(request):
    reservations = RoomReservation.objects.select_related("guest", "room_type", "room").all().order_by("-created_at")

    status_filter = request.GET.get("status")
    search_query = request.GET.get("q")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if status_filter:
        reservations = reservations.filter(status=status_filter)
    if search_query:
        reservations = reservations.filter(
            Q(guest__username__icontains=search_query) |
            Q(guest__first_name__icontains=search_query) |
            Q(guest__last_name__icontains=search_query) |
            Q(room_type__name__icontains=search_query) |
            Q(room__room_number__icontains=search_query)
        )
    if date_from:
        reservations = reservations.filter(check_in__gte=date_from)
    if date_to:
        reservations = reservations.filter(check_out__lte=date_to)

    paginator = Paginator(reservations, 15)
    page = request.GET.get("page")
    reservations = paginator.get_page(page)

    return render(request, "hotel/manager/reservations.html", {
        "reservations": reservations,
        "status_filter": status_filter,
        "search_query": search_query,
    })


@manager_required
def manager_reservation_detail(request, pk):
    reservation = get_object_or_404(RoomReservation.objects.select_related("guest", "room_type", "room"), pk=pk)
    available_rooms = []
    if reservation.room_type:
        booked_ids = RoomReservation.objects.filter(
            room_type=reservation.room_type,
            status__in=["pending", "confirmed"],
            check_in__lt=reservation.check_out,
            check_out__gt=reservation.check_in,
        ).exclude(pk=reservation.pk).values_list("room_id", flat=True)
        available_rooms = Room.objects.filter(
            room_type=reservation.room_type,
            is_active=True,
        ).exclude(status="inactive").exclude(
            id__in=booked_ids
        ).order_by("room_number")
    return render(request, "hotel/manager/reservation_detail.html", {
        "reservation": reservation,
        "available_rooms": available_rooms,
    })


@manager_required
def manager_update_reservation_status(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(RoomReservation.Status.choices):
            reservation.status = new_status
            reservation.save()
            messages.success(request, f"Reservation status updated to {reservation.get_status_display()}.")
        return redirect("hotel:manager_reservation_detail", pk=reservation.pk)
    return redirect("hotel:manager_reservations")


@manager_required
def manager_common_reservations(request):
    reservations = CommonAreaReservation.objects.select_related("guest", "common_area").all().order_by("-created_at")

    status_filter = request.GET.get("status")
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    paginator = Paginator(reservations, 15)
    page = request.GET.get("page")
    reservations = paginator.get_page(page)

    return render(request, "hotel/manager/common_reservations.html", {
        "reservations": reservations,
        "status_filter": status_filter,
    })


@manager_required
def manager_tickets(request):
    tickets = Ticket.objects.select_related("guest", "assigned_staff").all().order_by("-created_at")

    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("q")

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if category_filter:
        tickets = tickets.filter(category=category_filter)
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(guest__username__icontains=search_query)
        )

    paginator = Paginator(tickets, 15)
    page = request.GET.get("page")
    tickets = paginator.get_page(page)

    return render(request, "hotel/manager/tickets.html", {
        "tickets": tickets,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "category_filter": category_filter,
        "search_query": search_query,
        "ticket_status_choices": Ticket.Status.choices,
    })


@manager_required
def manager_ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("guest", "assigned_staff", "room"), pk=pk)
    notes = ticket.notes.select_related("user").all()
    assign_form = TicketAssignForm(instance=ticket)
    return render(request, "hotel/manager/ticket_detail.html", {
        "ticket": ticket,
        "notes": notes,
        "assign_form": assign_form,
    })


@manager_required
def manager_assign_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == "POST":
        form = TicketAssignForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            if ticket.assigned_staff and ticket.status == "open":
                ticket.status = "assigned"
                ticket.save()
            messages.success(request, "Ticket updated successfully.")
    return redirect("hotel:manager_ticket_detail", pk=ticket.pk)


@manager_required
def manager_update_ticket_status(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Ticket.Status.choices):
            ticket.status = new_status
            ticket.save()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True, "status": ticket.get_status_display()})
            messages.success(request, f"Ticket status updated to {ticket.get_status_display()}.")
    return redirect("hotel:manager_ticket_detail", pk=ticket.pk)


@manager_required
def manager_reports(request):
    total_guests = User.objects.filter(role="guest").count()
    total_staff = User.objects.filter(role="staff").count()
    total_rooms = Room.objects.filter(is_active=True).count()
    available_rooms = Room.objects.filter(status="available", is_active=True).count()

    reservations_by_status = RoomReservation.objects.values("status").annotate(count=Count("id"))
    tickets_by_status = Ticket.objects.values("status").annotate(count=Count("id"))
    tickets_by_priority = Ticket.objects.values("priority").annotate(count=Count("id"))

    revenue_data = (
        RoomReservation.objects.filter(status__in=["confirmed", "completed"])
        .values("room_type__name")
        .annotate(total=Sum("total_price"), count=Count("id"))
    )

    monthly_reservations = (
        RoomReservation.objects.filter(status__in=["confirmed", "completed"])
        .extra(select={"month": "strftime('%%Y-%%m', created_at)"})
        .values("month")
        .annotate(count=Count("id"), revenue=Sum("total_price"))
        .order_by("month")
    )

    context = {
        "total_guests": total_guests,
        "total_staff": total_staff,
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "reservations_by_status": list(reservations_by_status),
        "tickets_by_status": list(tickets_by_status),
        "tickets_by_priority": list(tickets_by_priority),
        "revenue_data": list(revenue_data),
        "monthly_reservations": list(monthly_reservations),
    }
    return render(request, "hotel/manager/reports.html", context)


# ─── Manager: Assign Room to Reservation ───────────────────────────────────


@manager_required
def manager_assign_room(request, pk):
    reservation = get_object_or_404(RoomReservation, pk=pk)
    if request.method == "POST":
        form = RoomAssignForm(request.POST, reservation=reservation)
        if form.is_valid():
            room = form.cleaned_data["room"]
            if room:
                reservation.room = room
                if reservation.status == "pending":
                    reservation.status = "confirmed"
                reservation.save()
                messages.success(request, f"Room {room.room_number} assigned to reservation #{reservation.id}.")
            else:
                reservation.room = None
                reservation.save()
                messages.success(request, "Room unassigned from reservation.")
        else:
            messages.error(request, "Could not assign room. Please check for conflicts.")
    return redirect("hotel:manager_reservation_detail", pk=reservation.pk)


# ─── Hotel Offers (Public) ─────────────────────────────────────────────────


def offers_list(request):
    offers = HotelOffer.objects.filter(is_active=True).select_related("common_area").order_by("offer_type", "title")
    offer_type = request.GET.get("type")
    if offer_type:
        offers = offers.filter(offer_type=offer_type)
    return render(request, "hotel/public/offers.html", {
        "offers": offers,
        "offer_type_choices": HotelOffer.OfferType.choices,
        "current_type": offer_type,
    })


# ─── Manager: Hotel Offer CRUD ──────────────────────────────────────────────


@manager_required
def manager_offers(request):
    offers = HotelOffer.objects.all().select_related("common_area").order_by("-created_at")
    return render(request, "hotel/manager/offers_list.html", {"offers": offers})


@manager_required
def manager_offer_create(request):
    if request.method == "POST":
        form = HotelOfferForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer created successfully.")
            return redirect("hotel:manager_offers")
    else:
        form = HotelOfferForm()
    return render(request, "hotel/manager/offer_form.html", {"form": form, "title": "Create Offer"})


@manager_required
def manager_offer_edit(request, pk):
    offer = get_object_or_404(HotelOffer, pk=pk)
    if request.method == "POST":
        form = HotelOfferForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer updated successfully.")
            return redirect("hotel:manager_offers")
    else:
        form = HotelOfferForm(instance=offer)
    return render(request, "hotel/manager/offer_form.html", {"form": form, "title": "Edit Offer"})


@manager_required
def manager_offer_delete(request, pk):
    offer = get_object_or_404(HotelOffer, pk=pk)
    if request.method == "POST":
        offer.delete()
        messages.success(request, "Offer deleted successfully.")
        return redirect("hotel:manager_offers")
    return render(request, "hotel/manager/offer_confirm_delete.html", {"offer": offer})
