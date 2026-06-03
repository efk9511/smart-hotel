from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import (
    Announcement, CommonArea, CommonAreaReservation, HotelOffer, Room,
    RoomReservation, RoomType, Ticket, TicketNote,
)
from .forms import (
    AnnouncementForm, CommonAreaReservationForm, RoomForm, RoomReservationForm,
    RoomTypeForm, TicketForm, UserCreateForm, UserRegistrationForm,
)

User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="testguest", password="test123", role="guest"
        )
        self.staff = User.objects.create_user(
            username="teststaff", password="test123", role="staff"
        )
        self.manager = User.objects.create_user(
            username="testmgr", password="test123", role="manager"
        )

    def test_guest_role(self):
        self.assertTrue(self.guest.is_guest())
        self.assertFalse(self.guest.is_staff)
        self.assertFalse(self.guest.is_manager())
        self.assertFalse(self.guest.is_staff_role())

    def test_staff_role(self):
        self.assertFalse(self.staff.is_staff)
        self.assertFalse(self.staff.is_manager())
        self.assertTrue(self.staff.is_staff_role())

    def test_manager_role(self):
        self.assertTrue(self.manager.is_manager())
        self.assertFalse(self.manager.is_staff_role())

    def test_user_str(self):
        self.assertIn("testguest", str(self.guest))


class RegistrationTests(TestCase):
    def test_user_registration(self):
        response = self.client.post(reverse("hotel:register"), {
            "username": "newuser",
            "email": "new@test.com",
            "first_name": "New",
            "last_name": "User",
            "phone_number": "555-1234",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.role, "guest")

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse("hotel:register"), {
            "username": "baduser",
            "password1": "ComplexPass123!",
            "password2": "DifferentPass123!",
        })
        self.assertEqual(response.status_code, 200)

    def test_registration_empty_username(self):
        response = self.client.post(reverse("hotel:register"), {
            "username": "",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        })
        self.assertEqual(response.status_code, 200)


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="logintest", password="test123", role="guest"
        )

    def test_login_success(self):
        response = self.client.post(reverse("hotel:login"), {
            "username": "logintest",
            "password": "test123",
        })
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post(reverse("hotel:login"), {
            "username": "logintest",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="logintest", password="test123")
        response = self.client.get(reverse("hotel:logout"))
        self.assertEqual(response.status_code, 302)


class AuthorizationTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="guest_auth", password="test123", role="guest"
        )
        self.staff = User.objects.create_user(
            username="staff_auth", password="test123", role="staff"
        )
        self.manager = User.objects.create_user(
            username="mgr_auth", password="test123", role="manager"
        )

    def test_guest_cannot_access_manager_dashboard(self):
        self.client.login(username="guest_auth", password="test123")
        response = self.client.get(reverse("hotel:manager_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_staff_cannot_access_manager_dashboard(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:manager_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_manager_can_access_manager_dashboard(self):
        self.client.login(username="mgr_auth", password="test123")
        response = self.client.get(reverse("hotel:manager_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_guest_dashboard(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:guest_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_guest_cannot_access_staff_dashboard(self):
        self.client.login(username="guest_auth", password="test123")
        response = self.client.get(reverse("hotel:staff_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_guest_cannot_access_manager_users(self):
        self.client.login(username="guest_auth", password="test123")
        response = self.client.get(reverse("hotel:manager_users"))
        self.assertEqual(response.status_code, 302)

    def test_staff_cannot_access_manager_users(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:manager_users"))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_redirected_to_login(self):
        response = self.client.get(reverse("hotel:guest_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access_staff_dashboard(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:staff_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_access_staff_tickets(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:staff_tickets"))
        self.assertEqual(response.status_code, 200)

    def test_staff_sees_navigation_links_on_dashboard(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:staff_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tickets")
        self.assertContains(response, "Dashboard")

    def test_staff_sees_navigation_links_in_base(self):
        self.client.login(username="staff_auth", password="test123")
        response = self.client.get(reverse("hotel:staff_tickets"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("hotel:staff_dashboard"))


class PublicPageTests(TestCase):
    def test_homepage_accessible(self):
        response = self.client.get(reverse("hotel:home"))
        self.assertEqual(response.status_code, 200)

    def test_about_page_accessible(self):
        response = self.client.get(reverse("hotel:about"))
        self.assertEqual(response.status_code, 200)

    def test_room_types_page_accessible(self):
        response = self.client.get(reverse("hotel:room_type_list"))
        self.assertEqual(response.status_code, 200)

    def test_login_page_accessible(self):
        response = self.client.get(reverse("hotel:login"))
        self.assertEqual(response.status_code, 200)

    def test_register_page_accessible(self):
        response = self.client.get(reverse("hotel:register"))
        self.assertEqual(response.status_code, 200)


class TicketTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="ticket_guest", password="test123", role="guest"
        )
        self.staff = User.objects.create_user(
            username="ticket_staff", password="test123", role="staff"
        )
        self.client.login(username="ticket_guest", password="test123")

    def test_guest_can_create_ticket(self):
        response = self.client.post(reverse("hotel:create_ticket"), {
            "title": "Test Issue",
            "description": "This is a test ticket",
            "category": "maintenance",
            "priority": "medium",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(title="Test Issue").exists())

    def test_ticket_created_for_correct_guest(self):
        self.client.post(reverse("hotel:create_ticket"), {
            "title": "My Ticket",
            "description": "Description",
            "category": "complaint",
            "priority": "high",
        })
        ticket = Ticket.objects.get(title="My Ticket")
        self.assertEqual(ticket.guest, self.guest)

    def test_staff_only_sees_assigned_tickets(self):
        ticket = Ticket.objects.create(
            guest=self.guest,
            title="Assigned Ticket",
            description="Desc",
            assigned_staff=self.staff,
            status="assigned",
        )
        Ticket.objects.create(
            guest=self.guest,
            title="Unassigned Ticket",
            description="Desc",
            status="open",
        )
        self.client.login(username="ticket_staff", password="test123")
        response = self.client.get(reverse("hotel:staff_tickets"))
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets.object_list), 1)
        self.assertEqual(tickets.object_list[0].title, "Assigned Ticket")

    def test_guest_sees_own_tickets(self):
        Ticket.objects.create(guest=self.guest, title="My Ticket", description="Desc")
        response = self.client.get(reverse("hotel:my_tickets"))
        self.assertEqual(len(response.context["tickets"]), 1)

    def test_guest_cannot_see_other_ticket(self):
        other = User.objects.create_user(username="other", password="test123", role="guest")
        ticket = Ticket.objects.create(guest=other, title="Other Ticket", description="Desc")
        response = self.client.get(reverse("hotel:ticket_detail", args=[ticket.id]))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_update_ticket_status(self):
        ticket = Ticket.objects.create(
            guest=self.guest, title="Status Test", description="Desc",
            assigned_staff=self.staff, status="assigned",
        )
        self.client.login(username="ticket_staff", password="test123")
        response = self.client.post(
            reverse("hotel:staff_update_ticket_status", args=[ticket.id]),
            {"status": "in_progress"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "in_progress")

    def test_staff_can_add_note(self):
        ticket = Ticket.objects.create(
            guest=self.guest, title="Note Test", description="Desc",
            assigned_staff=self.staff, status="assigned",
        )
        self.client.login(username="ticket_staff", password="test123")
        response = self.client.post(
            reverse("hotel:staff_add_note", args=[ticket.id]),
            {"note": "Working on it"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TicketNote.objects.filter(ticket=ticket, note="Working on it").exists())

    def test_ticket_str(self):
        ticket = Ticket.objects.create(guest=self.guest, title="Test", description="Desc")
        self.assertIn("Test", str(ticket))

    def test_ticket_note_str(self):
        ticket = Ticket.objects.create(guest=self.guest, title="Test", description="Desc")
        note = TicketNote.objects.create(ticket=ticket, user=self.guest, note="Hello")
        self.assertIn("#" + str(ticket.id), str(note))
        self.assertIn(self.guest.username, str(note))


class ReservationValidationTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="res_guest", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Test Room",
            description="Test",
            price_per_night=Decimal("100.00"),
            capacity=2,
        )

    def test_check_out_after_check_in_valid(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 3),
            number_of_guests=1,
        )
        try:
            reservation.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly")

    def test_check_out_before_check_in_invalid(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 3),
            check_out=date(2030, 6, 1),
            number_of_guests=1,
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_guests_exceed_capacity_invalid(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 3),
            number_of_guests=5,
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_check_in_in_past_invalid(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2020, 1, 1),
            check_out=date(2020, 1, 3),
            number_of_guests=1,
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_number_of_guests_zero_invalid(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 3),
            number_of_guests=0,
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_nights_calculation(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 4),
            number_of_guests=1,
        )
        self.assertEqual(reservation.nights(), 3)

    def test_total_price_calculation(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 4),
            number_of_guests=1,
        )
        reservation.save()
        self.assertEqual(reservation.total_price, Decimal("300.00"))

    def test_reservation_str(self):
        reservation = RoomReservation(
            guest=self.guest,
            room_type=self.room_type,
            check_in=date(2030, 6, 1),
            check_out=date(2030, 6, 4),
            number_of_guests=1,
        )
        self.assertIn("Test Room", str(reservation))


class CommonAreaReservationValidationTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="ca_guest", password="test123", role="guest"
        )
        self.area = CommonArea.objects.create(
            name="Test Pool",
            description="Test",
            capacity=10,
            opening_time=time(8, 0),
            closing_time=time(22, 0),
        )

    def test_end_time_after_start_time_valid(self):
        res = CommonAreaReservation(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            number_of_people=2,
        )
        try:
            res.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly")

    def test_end_time_before_start_time_invalid(self):
        res = CommonAreaReservation(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(14, 0),
            end_time=time(12, 0),
            number_of_people=2,
        )
        with self.assertRaises(ValidationError):
            res.clean()

    def test_exceeds_area_capacity_invalid(self):
        res = CommonAreaReservation(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            number_of_people=20,
        )
        with self.assertRaises(ValidationError):
            res.clean()

    def test_outside_opening_hours_invalid(self):
        res = CommonAreaReservation(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(6, 0),
            end_time=time(7, 0),
            number_of_people=2,
        )
        with self.assertRaises(ValidationError):
            res.clean()

    def test_overlapping_reservation_invalid(self):
        CommonAreaReservation.objects.create(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            number_of_people=2,
            status="confirmed",
        )
        res = CommonAreaReservation(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(11, 0),
            end_time=time(13, 0),
            number_of_people=2,
        )
        with self.assertRaises(ValidationError):
            res.clean()

    def test_common_area_str(self):
        self.assertIn("Test Pool", str(self.area))

    def test_common_area_reservation_str(self):
        res = CommonAreaReservation(
            guest=self.guest,
            common_area=self.area,
            reservation_date=date(2030, 7, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            number_of_people=2,
        )
        self.assertIn("Test Pool", str(res))


class ManagerUserCRUDTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_crud", password="test123", role="manager"
        )
        self.client.login(username="mgr_crud", password="test123")

    def test_manager_can_list_users(self):
        response = self.client.get(reverse("hotel:manager_users"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.context)

    def test_manager_can_create_user(self):
        response = self.client.post(reverse("hotel:manager_user_create"), {
            "username": "newuser_mgr",
            "password": "ComplexPass123!",
            "role": "staff",
            "first_name": "New",
            "last_name": "Staff",
            "email": "newstaff@test.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser_mgr").exists())
        user = User.objects.get(username="newuser_mgr")
        self.assertEqual(user.role, "staff")

    def test_manager_can_create_manager_user(self):
        response = self.client.post(reverse("hotel:manager_user_create"), {
            "username": "another_mgr",
            "password": "ComplexPass123!",
            "role": "manager",
            "email": "another@test.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="another_mgr").exists())

    def test_manager_can_edit_user(self):
        user = User.objects.create_user(
            username="editable", password="test123", role="guest",
            first_name="Old",
        )
        response = self.client.post(
            reverse("hotel:manager_user_edit", args=[user.id]),
            {"username": "editable", "first_name": "Updated", "role": "guest"},
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Updated")

    def test_manager_can_delete_user(self):
        user = User.objects.create_user(
            username="deletable", password="test123", role="guest"
        )
        response = self.client.post(
            reverse("hotel:manager_user_delete", args=[user.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="deletable").exists())

    def test_manager_user_search_filter(self):
        User.objects.create_user(username="john", password="test123", role="guest", first_name="John")
        User.objects.create_user(username="jane", password="test123", role="staff", first_name="Jane")
        response = self.client.get(reverse("hotel:manager_users") + "?q=john")
        users = response.context["users"]
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].username, "john")

    def test_manager_user_role_filter(self):
        User.objects.create_user(username="staff1", password="test123", role="staff")
        response = self.client.get(reverse("hotel:manager_users") + "?role=staff")
        users = response.context["users"]
        for u in users:
            self.assertEqual(u.role, "staff")


class ManagerRoomTypeCRUDTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_rt", password="test123", role="manager"
        )
        self.client.login(username="mgr_rt", password="test123")

    def test_manager_can_list_room_types(self):
        response = self.client.get(reverse("hotel:manager_room_types"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("room_types", response.context)

    def test_manager_can_create_room_type(self):
        response = self.client.post(reverse("hotel:manager_room_type_create"), {
            "name": "Suite",
            "description": "Luxury suite",
            "price_per_night": "250.00",
            "capacity": 4,
            "amenities": "WiFi, TV, Mini-bar",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RoomType.objects.filter(name="Suite").exists())

    def test_manager_can_edit_room_type(self):
        rt = RoomType.objects.create(
            name="Basic", description="Basic room",
            price_per_night=Decimal("80"), capacity=2,
        )
        response = self.client.post(
            reverse("hotel:manager_room_type_edit", args=[rt.id]),
            {"name": "Updated", "description": "Updated", "price_per_night": "90.00", "capacity": 3},
        )
        self.assertEqual(response.status_code, 302)
        rt.refresh_from_db()
        self.assertEqual(rt.name, "Updated")

    def test_manager_can_delete_room_type(self):
        rt = RoomType.objects.create(
            name="DeleteMe", description="Test",
            price_per_night=Decimal("50"), capacity=1,
        )
        response = self.client.post(reverse("hotel:manager_room_type_delete", args=[rt.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RoomType.objects.filter(name="DeleteMe").exists())


class ManagerRoomCRUDTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_room", password="test123", role="manager"
        )
        self.client.login(username="mgr_room", password="test123")
        self.room_type = RoomType.objects.create(
            name="Standard", description="Standard room",
            price_per_night=Decimal("100"), capacity=2,
        )

    def test_manager_can_list_rooms(self):
        response = self.client.get(reverse("hotel:manager_rooms"))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_create_room(self):
        response = self.client.post(reverse("hotel:manager_room_create"), {
            "room_number": "101",
            "room_type": self.room_type.id,
            "floor": 1,
            "status": "available",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(room_number="101").exists())

    def test_manager_can_edit_room(self):
        room = Room.objects.create(
            room_number="102", room_type=self.room_type, floor=1,
        )
        response = self.client.post(
            reverse("hotel:manager_room_edit", args=[room.id]),
            {"room_number": "102A", "room_type": self.room_type.id, "floor": 2, "status": "maintenance"},
        )
        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        self.assertEqual(room.room_number, "102A")

    def test_manager_can_delete_room(self):
        room = Room.objects.create(
            room_number="103", room_type=self.room_type, floor=1,
        )
        response = self.client.post(reverse("hotel:manager_room_delete", args=[room.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Room.objects.filter(room_number="103").exists())


class ManagerGroupedRoomManagementTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="grp_mgr", password="test123", role="manager"
        )
        self.guest = User.objects.create_user(
            username="grp_guest", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Grouped Test Room", description="Test",
            price_per_night=Decimal("100"), capacity=2,
        )
        self.room1 = Room.objects.create(
            room_number="G01", room_type=self.room_type, floor=1, status="available",
        )
        self.room2 = Room.objects.create(
            room_number="G02", room_type=self.room_type, floor=1, status="maintenance",
        )
        self.room3 = Room.objects.create(
            room_number="G03", room_type=self.room_type, floor=1, status="inactive",
        )
        self.client.login(username="grp_mgr", password="test123")

    def test_manager_views_rooms_grouped_by_type(self):
        response = self.client.get(reverse("hotel:manager_rooms"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("type_data", response.context)
        # Should contain our room type
        types = response.context["type_data"]
        self.assertTrue(any(t["room_type"].id == self.room_type.id for t in types))

    def test_room_type_shows_correct_counts(self):
        response = self.client.get(reverse("hotel:manager_rooms"))
        types = response.context["type_data"]
        target = next(t for t in types if t["room_type"].id == self.room_type.id)
        self.assertEqual(target["total"], 3)
        self.assertEqual(target["counts"]["available"], 1)
        self.assertEqual(target["counts"]["maintenance"], 1)
        self.assertEqual(target["counts"]["inactive"], 1)

    def test_manager_can_change_status_maintenance_to_available(self):
        response = self.client.post(
            reverse("hotel:manager_room_change_status", args=[self.room2.id]),
            {"status": "available"},
        )
        self.assertEqual(response.status_code, 302)
        self.room2.refresh_from_db()
        self.assertEqual(self.room2.status, "available")

    def test_manager_cannot_set_reserved_room_to_available(self):
        today = timezone.now().date()
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room1,
            check_in=today - timedelta(days=1),
            check_out=today + timedelta(days=1),
            number_of_guests=1, status="confirmed",
        )
        self.room1.status = "available"
        self.room1.save()
        response = self.client.post(
            reverse("hotel:manager_room_change_status", args=[self.room1.id]),
            {"status": "maintenance"},
        )
        # Should succeed — can set to maintenance even with active reservation
        self.assertEqual(response.status_code, 302)
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.status, "maintenance")

        # But setting back to available should be blocked
        response = self.client.post(
            reverse("hotel:manager_room_change_status", args=[self.room1.id]),
            {"status": "available"},
        )
        self.room1.refresh_from_db()
        # Should still be maintenance (blocked)
        self.assertEqual(self.room1.status, "maintenance")

    def test_maintenance_room_excluded_from_auto_assign(self):
        self.room2.status = "maintenance"
        self.room2.save()
        future = timezone.now().date() + timedelta(days=10)
        available = self.room_type.get_available_rooms(future, future + timedelta(days=2))
        # G01 is available, G02 is maintenance, G03 is inactive
        room_numbers = [r.room_number for r in available]
        self.assertIn("G01", room_numbers)
        self.assertNotIn("G02", room_numbers)
        self.assertNotIn("G03", room_numbers)

    def test_non_manager_cannot_access_room_management(self):
        self.client.logout()
        staff = User.objects.create_user(
            username="grp_staff", password="test123", role="staff"
        )
        self.client.login(username="grp_staff", password="test123")
        response = self.client.get(reverse("hotel:manager_rooms"))
        self.assertNotEqual(response.status_code, 200)

    def test_auto_assignment_still_works_for_available_rooms(self):
        future = timezone.now().date() + timedelta(days=20)
        self.client.logout()
        self.client.login(username="grp_guest", password="test123")
        session = self.client.session
        session["reservation_data"] = {
            "room_type_id": self.room_type.id,
            "check_in": future.isoformat(),
            "check_out": (future + timedelta(days=2)).isoformat(),
            "guests": 1,
        }
        session.save()
        response = self.client.post(reverse("hotel:confirm_reservation"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            RoomReservation.objects.filter(
                guest=self.guest, room_type=self.room_type, status="confirmed"
            ).exists()
        )


class ManagerAnnouncementCRUDTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_ann", password="test123", role="manager"
        )
        self.client.login(username="mgr_ann", password="test123")

    def test_manager_can_list_announcements(self):
        response = self.client.get(reverse("hotel:manager_announcements"))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_create_announcement(self):
        response = self.client.post(reverse("hotel:manager_announcement_create"), {
            "title": "Pool Closed",
            "content": "The pool is closed for maintenance.",
            "target_audience": "all",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(title="Pool Closed").exists())

    def test_manager_can_edit_announcement(self):
        ann = Announcement.objects.create(
            title="Old Title",
            content="Old content",
            target_audience="all",
            created_by=self.manager,
        )
        response = self.client.post(
            reverse("hotel:manager_announcement_edit", args=[ann.id]),
            {"title": "New Title", "content": "New content", "target_audience": "guests"},
        )
        self.assertEqual(response.status_code, 302)
        ann.refresh_from_db()
        self.assertEqual(ann.title, "New Title")

    def test_manager_can_delete_announcement(self):
        ann = Announcement.objects.create(
            title="Delete Ann", content="Test", target_audience="all",
            created_by=self.manager,
        )
        response = self.client.post(reverse("hotel:manager_announcement_delete", args=[ann.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.filter(title="Delete Ann").exists())


class GuestReservationFlowTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="res_flow", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Deluxe", description="Deluxe room",
            price_per_night=Decimal("200"), capacity=3,
        )
        Room.objects.create(
            room_number="D01", room_type=self.room_type, floor=1,
        )

    def test_guest_can_start_reservation_session(self):
        self.client.login(username="res_flow", password="test123")
        response = self.client.get(reverse("hotel:start_reservation"))
        self.assertEqual(response.status_code, 200)

    def test_guest_can_confirm_reservation(self):
        self.client.login(username="res_flow", password="test123")
        session = self.client.session
        session["reservation_data"] = {
            "room_type_id": self.room_type.id,
            "check_in": "2030-08-01",
            "check_out": "2030-08-03",
            "guests": 2,
        }
        session.save()
        response = self.client.post(reverse("hotel:confirm_reservation"), {
            "number_of_guests": 2,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RoomReservation.objects.filter(guest=self.guest).exists())

    def test_guest_can_view_own_reservations(self):
        self.client.login(username="res_flow", password="test123")
        response = self.client.get(reverse("hotel:my_room_reservations"))
        self.assertEqual(response.status_code, 200)

    def test_guest_can_create_common_reservation(self):
        self.client.login(username="res_flow", password="test123")
        area = CommonArea.objects.create(
            name="Gym", description="Fitness center", capacity=5,
        )
        response = self.client.post(reverse("hotel:create_common_reservation"), {
            "common_area": area.id,
            "reservation_date": "2030-09-01",
            "start_time": "10:00",
            "end_time": "11:00",
            "number_of_people": 2,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommonAreaReservation.objects.filter(guest=self.guest).exists())


class ManagerReservationTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_res", password="test123", role="manager"
        )
        self.guest = User.objects.create_user(
            username="res_guest2", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Standard", description="Standard",
            price_per_night=Decimal("100"), capacity=2,
        )
        self.client.login(username="mgr_res", password="test123")

    def test_manager_can_list_reservations(self):
        response = self.client.get(reverse("hotel:manager_reservations"))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_view_reservation_detail(self):
        res = RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type,
            check_in=date(2030, 6, 1), check_out=date(2030, 6, 3),
            number_of_guests=1,
        )
        response = self.client.get(reverse("hotel:manager_reservation_detail", args=[res.id]))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_list_common_reservations(self):
        response = self.client.get(reverse("hotel:manager_common_reservations"))
        self.assertEqual(response.status_code, 200)


class ManagerTicketTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_tix", password="test123", role="manager"
        )
        self.guest = User.objects.create_user(
            username="tix_guest", password="test123", role="guest"
        )
        self.staff_user = User.objects.create_user(
            username="tix_staff", password="test123", role="staff"
        )
        self.client.login(username="mgr_tix", password="test123")

    def test_manager_can_list_tickets(self):
        response = self.client.get(reverse("hotel:manager_tickets"))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_view_ticket_detail(self):
        ticket = Ticket.objects.create(
            guest=self.guest, title="Mgr Ticket", description="Desc",
        )
        response = self.client.get(reverse("hotel:manager_ticket_detail", args=[ticket.id]))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_assign_ticket(self):
        ticket = Ticket.objects.create(
            guest=self.guest, title="Assign Me", description="Desc", status="open",
        )
        response = self.client.post(
            reverse("hotel:manager_assign_ticket", args=[ticket.id]),
            {"assigned_staff": self.staff_user.id, "priority": "medium", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.assigned_staff, self.staff_user)
        self.assertEqual(ticket.status, "assigned")

    def test_manager_ticket_search_filter(self):
        Ticket.objects.create(guest=self.guest, title="Broken AC", description="Desc")
        response = self.client.get(reverse("hotel:manager_tickets") + "?q=broken")
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets.object_list), 1)


class ReportsTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_rpt", password="test123", role="manager"
        )
        self.client.login(username="mgr_rpt", password="test123")

    def test_manager_can_access_reports(self):
        response = self.client.get(reverse("hotel:manager_reports"))
        self.assertEqual(response.status_code, 200)


class AnnouncementVisibilityTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="ann_guest", password="test123", role="guest"
        )
        self.manager = User.objects.create_user(
            username="ann_mgr", password="test123", role="manager"
        )
        Announcement.objects.create(
            title="All Announcement", content="For everyone", target_audience="all", is_active=True,
            created_by=self.manager,
        )
        Announcement.objects.create(
            title="Guest Only", content="For guests only", target_audience="guests", is_active=True,
            created_by=self.manager,
        )
        Announcement.objects.create(
            title="Staff Only", content="For staff", target_audience="staff", is_active=True,
            created_by=self.manager,
        )

    def test_guest_sees_all_and_guest_announcements(self):
        self.client.login(username="ann_guest", password="test123")
        response = self.client.get(reverse("hotel:home"))
        titles = [a.title for a in response.context["announcements"]] if "announcements" in response.context else []
        self.assertIn("All Announcement", titles)
        self.assertIn("Guest Only", titles)
        self.assertNotIn("Staff Only", titles)


class ProfileTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="prof_user", password="test123", role="guest",
            first_name="Old",
        )
        self.client.login(username="prof_user", password="test123")

    def test_guest_can_view_profile_page(self):
        response = self.client.get(reverse("hotel:guest_profile"))
        self.assertEqual(response.status_code, 200)

    def test_guest_can_update_profile(self):
        response = self.client.post(reverse("hotel:guest_profile"), {
            "username": "prof_user",
            "first_name": "Updated",
            "last_name": "Name",
            "email": "new@test.com",
        })
        self.assertEqual(response.status_code, 302)
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.first_name, "Updated")


class ThemeToggleTests(TestCase):
    def test_toggle_theme_light_to_dark(self):
        response = self.client.get(reverse("hotel:toggle_theme") + "?theme=dark")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.cookies.get("theme").value, "dark")

    def test_toggle_theme_dark_to_light(self):
        response = self.client.get(reverse("hotel:toggle_theme") + "?theme=light")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.cookies.get("theme").value, "light")


class APITests(TestCase):
    def test_api_room_types(self):
        RoomType.objects.create(
            name="API Room", description="Test",
            price_per_night=Decimal("150"), capacity=2,
        )
        response = self.client.get(reverse("hotel:api_room_types"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_api_common_areas(self):
        CommonArea.objects.create(
            name="API Area", description="Test", capacity=10,
        )
        response = self.client.get(reverse("hotel:api_common_areas"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_api_room_types_detail(self):
        rt = RoomType.objects.create(
            name="Detail Room", description="Detail",
            price_per_night=Decimal("200"), capacity=3,
        )
        response = self.client.get(reverse("hotel:api_room_types"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Detail Room")


class FormValidationTests(TestCase):
    def setUp(self):
        self.room_type = RoomType.objects.create(
            name="Form Test", description="Test",
            price_per_night=Decimal("100"), capacity=2,
        )

    def test_room_reservation_form_check_out_before_check_in(self):
        form = RoomReservationForm(data={
            "room_type": self.room_type.id,
            "check_in": "2030-06-10",
            "check_out": "2030-06-05",
            "number_of_guests": 1,
        })
        self.assertFalse(form.is_valid())

    def test_room_reservation_form_exceeds_capacity(self):
        form = RoomReservationForm(data={
            "room_type": self.room_type.id,
            "check_in": "2030-06-01",
            "check_out": "2030-06-03",
            "number_of_guests": 10,
        })
        self.assertFalse(form.is_valid())

    def test_common_area_form_end_before_start(self):
        area = CommonArea.objects.create(name="Form Pool", capacity=10)
        form = CommonAreaReservationForm(data={
            "common_area": area.id,
            "reservation_date": "2030-07-01",
            "start_time": "14:00",
            "end_time": "12:00",
            "number_of_people": 2,
        })
        self.assertFalse(form.is_valid())


class ModelStrTests(TestCase):
    def test_room_type_str(self):
        rt = RoomType(name="TestType", description="Test")
        self.assertIn("TestType", str(rt))

    def test_room_str(self):
        rt = RoomType(name="Test", description="Test")
        room = Room(room_number="R01", room_type=rt)
        self.assertIn("R01", str(room))

    def test_announcement_str(self):
        ann = Announcement(title="Test Announcement")
        self.assertIn("Test Announcement", str(ann))


class SearchFilterTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="sf_guest", password="test123", role="guest"
        )
        self.staff = User.objects.create_user(
            username="sf_staff", password="test123", role="staff"
        )
        self.client.login(username="sf_staff", password="test123")

    def test_staff_ticket_search(self):
        Ticket.objects.create(guest=self.guest, title="AC Repair", description="Hot", assigned_staff=self.staff, status="assigned")
        Ticket.objects.create(guest=self.guest, title="Plumbing", description="Wet", assigned_staff=self.staff, status="assigned")
        response = self.client.get(reverse("hotel:staff_tickets") + "?q=AC")
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets.object_list), 1)

    def test_staff_ticket_status_filter(self):
        Ticket.objects.create(guest=self.guest, title="Open Ticket", description="Test", assigned_staff=self.staff, status="open")
        Ticket.objects.create(guest=self.guest, title="Resolved Ticket", description="Test", assigned_staff=self.staff, status="resolved")
        response = self.client.get(reverse("hotel:staff_tickets") + "?status=open")
        tickets = response.context["tickets"]
        for t in tickets.object_list:
            self.assertEqual(t.status, "open")

    def test_staff_ticket_priority_filter(self):
        Ticket.objects.create(guest=self.guest, title="High Priority", description="Test", assigned_staff=self.staff, priority="high")
        Ticket.objects.create(guest=self.guest, title="Low Priority", description="Test", assigned_staff=self.staff, priority="low")
        response = self.client.get(reverse("hotel:staff_tickets") + "?priority=high")
        tickets = response.context["tickets"]
        for t in tickets.object_list:
            self.assertEqual(t.priority, "high")


class ManagerReportsFilterTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr_rpt2", password="test123", role="manager"
        )
        self.client.login(username="mgr_rpt2", password="test123")

    def test_reports_with_date_filter(self):
        response = self.client.get(reverse("hotel:manager_reports") + "?date_from=2030-01-01&date_to=2030-12-31")
        self.assertEqual(response.status_code, 200)


class PrintReservationTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="print_guest", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Print Room", description="Test",
            price_per_night=Decimal("100"), capacity=2,
        )
        self.client.login(username="print_guest", password="test123")

    def test_print_reservation_page(self):
        res = RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type,
            check_in=date(2030, 6, 1), check_out=date(2030, 6, 3),
            number_of_guests=1,
        )
        response = self.client.get(reverse("hotel:print_reservation", args=[res.id]))
        self.assertEqual(response.status_code, 200)


class HotelOfferModelTests(TestCase):
    def setUp(self):
        self.offer = HotelOffer.objects.create(
            title="Test Offer",
            description="A test offer description",
            offer_type="dining",
            is_free_for_guests=True,
        )

    def test_offer_creation(self):
        self.assertEqual(str(self.offer), "Test Offer")
        self.assertTrue(self.offer.is_free_for_guests)

    def test_offer_type_choices(self):
        self.assertEqual(self.offer.get_offer_type_display(), "Dining")


class OffersPublicPageTests(TestCase):
    def setUp(self):
        HotelOffer.objects.create(
            title="Sunset Cocktails",
            description="Enjoy sunset views",
            offer_type="entertainment",
            is_free_for_guests=True,
            is_active=True,
        )
        HotelOffer.objects.create(
            title="Spa Package",
            description="Relax and unwind",
            offer_type="spa",
            price=Decimal("100.00"),
            is_free_for_guests=False,
            is_active=True,
        )

    def test_offers_page_accessible(self):
        response = self.client.get(reverse("hotel:offers_list"))
        self.assertEqual(response.status_code, 200)

    def test_offers_page_contains_offers(self):
        response = self.client.get(reverse("hotel:offers_list"))
        self.assertContains(response, "Sunset Cocktails")
        self.assertContains(response, "Spa Package")

    def test_offers_page_filter_by_type(self):
        response = self.client.get(reverse("hotel:offers_list") + "?type=spa")
        self.assertContains(response, "Spa Package")
        self.assertNotContains(response, "Sunset Cocktails")

    def test_inactive_offer_not_shown(self):
        HotelOffer.objects.create(
            title="Hidden Offer", description="Hidden",
            is_active=False,
        )
        response = self.client.get(reverse("hotel:offers_list"))
        self.assertNotContains(response, "Hidden Offer")


class ManagerOfferCRUDTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="offer_mgr", password="test123", role="manager"
        )
        self.client.login(username="offer_mgr", password="test123")

    def test_manager_can_list_offers(self):
        response = self.client.get(reverse("hotel:manager_offers"))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_create_offer(self):
        response = self.client.post(reverse("hotel:manager_offer_create"), {
            "title": "New Offer",
            "description": "New offer description",
            "offer_type": "dining",
            "is_free_for_guests": True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(HotelOffer.objects.filter(title="New Offer").exists())

    def test_manager_can_edit_offer(self):
        offer = HotelOffer.objects.create(title="Edit Me", description="Original")
        response = self.client.post(
            reverse("hotel:manager_offer_edit", args=[offer.id]),
            {"title": "Edited", "description": "Updated", "offer_type": "spa", "is_free_for_guests": False},
        )
        self.assertEqual(response.status_code, 302)
        offer.refresh_from_db()
        self.assertEqual(offer.title, "Edited")

    def test_manager_can_delete_offer(self):
        offer = HotelOffer.objects.create(title="Delete Me", description="Test")
        response = self.client.post(reverse("hotel:manager_offer_delete", args=[offer.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(HotelOffer.objects.filter(title="Delete Me").exists())


class ManagerAssignRoomTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="assign_mgr", password="test123", role="manager"
        )
        self.guest = User.objects.create_user(
            username="assign_guest", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Assign Suite", description="Test",
            price_per_night=Decimal("200"), capacity=2,
        )
        self.room = Room.objects.create(
            room_number="A01", room_type=self.room_type, floor=1, status="available",
        )
        self.reservation = RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type,
            check_in=date(2035, 6, 1), check_out=date(2035, 6, 3),
            number_of_guests=1, status="pending",
        )

    def test_manager_can_assign_room(self):
        self.client.login(username="assign_mgr", password="test123")
        response = self.client.post(
            reverse("hotel:manager_assign_room", args=[self.reservation.id]),
            {"room": self.room.id},
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.room, self.room)
        self.assertEqual(self.reservation.status, "confirmed")

    def test_manager_can_unassign_room(self):
        self.client.login(username="assign_mgr", password="test123")
        self.reservation.room = self.room
        self.reservation.save()
        response = self.client.post(
            reverse("hotel:manager_assign_room", args=[self.reservation.id]),
            {"room": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertIsNone(self.reservation.room)

    def test_manager_cannot_assign_overlapping_room(self):
        self.client.login(username="assign_mgr", password="test123")
        overlapping = RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=date(2035, 5, 30), check_out=date(2035, 6, 5),
            number_of_guests=1, status="confirmed",
        )
        response = self.client.post(
            reverse("hotel:manager_assign_room", args=[self.reservation.id]),
            {"room": self.room.id},
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertIsNone(self.reservation.room)

    def test_non_manager_cannot_assign_room(self):
        staff = User.objects.create_user(
            username="assign_staff", password="test123", role="staff"
        )
        self.client.login(username="assign_staff", password="test123")
        response = self.client.post(
            reverse("hotel:manager_assign_room", args=[self.reservation.id]),
            {"room": self.room.id},
        )
        self.assertEqual(response.status_code, 302)
        # Should redirect away (not to the detail page) because staff cannot access
        self.assertNotEqual(response.url, reverse("hotel:manager_reservation_detail", args=[self.reservation.id]))


class RoomAvailabilityTests(TestCase):
    def setUp(self):
        self.room_type = RoomType.objects.create(
            name="Availability Suite", description="Test",
            price_per_night=Decimal("200"), capacity=2,
        )
        self.room1 = Room.objects.create(
            room_number="V01", room_type=self.room_type, floor=1, status="available",
        )
        self.room2 = Room.objects.create(
            room_number="V02", room_type=self.room_type, floor=1, status="available",
        )
        self.room3 = Room.objects.create(
            room_number="V03", room_type=self.room_type, floor=2, status="maintenance",
        )
        self.guest = User.objects.create_user(
            username="avail_guest", password="test123", role="guest"
        )

    def test_get_available_rooms_returns_active_available(self):
        rooms = self.room_type.get_available_rooms(date(2035, 7, 1), date(2035, 7, 3))
        self.assertIn(self.room1, rooms)
        self.assertIn(self.room2, rooms)
        self.assertNotIn(self.room3, rooms)

    def test_get_available_rooms_excludes_overlapping(self):
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room1,
            check_in=date(2035, 7, 1), check_out=date(2035, 7, 3),
            number_of_guests=1, status="confirmed",
        )
        rooms = self.room_type.get_available_rooms(date(2035, 7, 1), date(2035, 7, 3))
        self.assertNotIn(self.room1, rooms)
        self.assertIn(self.room2, rooms)

    def test_cancelled_does_not_block_availability(self):
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room1,
            check_in=date(2035, 7, 1), check_out=date(2035, 7, 3),
            number_of_guests=1, status="cancelled",
        )
        rooms = self.room_type.get_available_rooms(date(2035, 7, 1), date(2035, 7, 3))
        self.assertIn(self.room1, rooms)

    def test_completed_does_not_block_availability(self):
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room1,
            check_in=date(2035, 7, 1), check_out=date(2035, 7, 3),
            number_of_guests=1, status="completed",
        )
        rooms = self.room_type.get_available_rooms(date(2035, 7, 1), date(2035, 7, 3))
        self.assertIn(self.room1, rooms)

    def test_available_rooms_count_returns_correct_number(self):
        count = self.room_type.available_rooms_count(date(2035, 7, 1), date(2035, 7, 3))
        self.assertEqual(count, 2)

    def test_get_available_rooms_ordered_by_floor_then_room(self):
        rooms = self.room_type.get_available_rooms(date(2035, 7, 1), date(2035, 7, 3))
        self.assertEqual(list(rooms), [self.room1, self.room2])


class AutoAssignRoomTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="auto_guest", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Auto Suite", description="Test",
            price_per_night=Decimal("200"), capacity=2,
        )
        self.room = Room.objects.create(
            room_number="Z01", room_type=self.room_type, floor=1, status="available",
        )

    def test_confirm_reservation_auto_assigns_room(self):
        self.client.login(username="auto_guest", password="test123")
        session = self.client.session
        session["reservation_data"] = {
            "room_type_id": self.room_type.id,
            "check_in": "2035-08-01",
            "check_out": "2035-08-03",
            "guests": 1,
        }
        session.save()
        response = self.client.post(reverse("hotel:confirm_reservation"))
        self.assertEqual(response.status_code, 302)
        reservation = RoomReservation.objects.get(guest=self.guest)
        self.assertEqual(reservation.room, self.room)
        self.assertEqual(reservation.status, "confirmed")

    def test_auto_assigned_room_matches_room_type(self):
        self.client.login(username="auto_guest", password="test123")
        other_type = RoomType.objects.create(
            name="Other Suite", description="Test",
            price_per_night=Decimal("300"), capacity=2,
        )
        Room.objects.create(
            room_number="Y01", room_type=other_type, floor=1, status="available",
        )
        session = self.client.session
        session["reservation_data"] = {
            "room_type_id": self.room_type.id,
            "check_in": "2035-08-01",
            "check_out": "2035-08-03",
            "guests": 1,
        }
        session.save()
        response = self.client.post(reverse("hotel:confirm_reservation"))
        self.assertEqual(response.status_code, 302)
        reservation = RoomReservation.objects.get(guest=self.guest)
        self.assertEqual(reservation.room.room_type, self.room_type)

    def test_no_rooms_available_shows_error(self):
        self.client.login(username="auto_guest", password="test123")
        # Pre-book the only room
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=date(2035, 8, 1), check_out=date(2035, 8, 3),
            number_of_guests=1, status="confirmed",
        )
        session = self.client.session
        session["reservation_data"] = {
            "room_type_id": self.room_type.id,
            "check_in": "2035-08-01",
            "check_out": "2035-08-03",
            "guests": 1,
        }
        session.save()
        response = self.client.post(reverse("hotel:confirm_reservation"))
        # Should redirect back to start because no rooms available
        self.assertRedirects(response, reverse("hotel:start_reservation"))
        # Only the pre-booked reservation should exist, no new one created
        self.assertEqual(RoomReservation.objects.filter(guest=self.guest).count(), 1)

    def test_availability_shown_on_start_page(self):
        self.client.login(username="auto_guest", password="test123")
        url = reverse("hotel:start_reservation")
        response = self.client.get(url + f"?room_type={self.room_type.id}&check_in=2035-08-01&check_out=2035-08-03")
        self.assertEqual(response.status_code, 200)
        self.assertIn("room_type_availability", response.context)
        avail = response.context["room_type_availability"]
        self.assertIn(self.room_type.id, avail)
        self.assertEqual(avail[self.room_type.id]["available"], 1)

    def test_availability_shows_sold_out(self):
        self.client.login(username="auto_guest", password="test123")
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=date(2035, 8, 1), check_out=date(2035, 8, 3),
            number_of_guests=1, status="confirmed",
        )
        url = reverse("hotel:start_reservation")
        response = self.client.get(url + f"?room_type={self.room_type.id}&check_in=2035-08-01&check_out=2035-08-03")
        avail = response.context["room_type_availability"]
        self.assertEqual(avail[self.room_type.id]["available"], 0)

    def test_start_reservation_blocks_when_no_rooms(self):
        self.client.login(username="auto_guest", password="test123")
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=date(2035, 8, 1), check_out=date(2035, 8, 3),
            number_of_guests=1, status="confirmed",
        )
        response = self.client.post(reverse("hotel:start_reservation"), {
            "room_type": self.room_type.id,
            "check_in": "2035-08-01",
            "check_out": "2035-08-03",
            "guests": 1,
        })
        self.assertRedirects(response, reverse("hotel:start_reservation"))
        # Only the pre-booked reservation exists, no room_type_id was stored in session
        self.assertEqual(RoomReservation.objects.filter(guest=self.guest).count(), 1)
        self.assertIsNone(self.client.session.get("reservation_data"))

    def test_manager_can_still_assign_after_auto_assign(self):
        """Manager can change the assigned room after auto-assignment"""
        self.client.login(username="auto_guest", password="test123")
        session = self.client.session
        session["reservation_data"] = {
            "room_type_id": self.room_type.id,
            "check_in": "2035-08-01",
            "check_out": "2035-08-03",
            "guests": 1,
        }
        session.save()
        response = self.client.post(reverse("hotel:confirm_reservation"))
        reservation = RoomReservation.objects.get(guest=self.guest)

        # Manager can reassign
        manager = User.objects.create_user(
            username="reassign_mgr", password="test123", role="manager"
        )
        self.client.login(username="reassign_mgr", password="test123")
        room2 = Room.objects.create(
            room_number="Z02", room_type=self.room_type, floor=1, status="available",
        )
        response = self.client.post(
            reverse("hotel:manager_assign_room", args=[reservation.id]),
            {"room": room2.id},
        )
        self.assertEqual(response.status_code, 302)
        reservation.refresh_from_db()
        self.assertEqual(reservation.room, room2)


class DemoAvailabilityBlockingTests(TestCase):
    """Tests that verify the demo blocking scenario works correctly.

    The seed data blocks all rooms of Presidential Sea View Suite and
    Executive Business Room for 2026-07-10 to 2026-07-15.
    These tests recreate that scenario to verify availability logic.
    """
    def setUp(self):
        self.guest = User.objects.create_user(
            username="demo_guest", password="test123", role="guest"
        )
        # Create room types matching the seed data
        self.rt_presidential = RoomType.objects.create(
            name="Presidential Sea View Suite", description="Test",
            price_per_night=Decimal("950"), capacity=4,
        )
        self.rt_executive = RoomType.objects.create(
            name="Executive Business Room", description="Test",
            price_per_night=Decimal("400"), capacity=2,
        )
        self.rt_standard = RoomType.objects.create(
            name="Standard City Room", description="Test",
            price_per_night=Decimal("180"), capacity=2,
        )
        self.rooms_presidential = []
        for i in range(6):
            room = Room.objects.create(
                room_number=f"P{i+1:02d}", room_type=self.rt_presidential,
                floor=11 + i // 3, status="available",
            )
            self.rooms_presidential.append(room)
        self.rooms_executive = []
        for i in range(6):
            room = Room.objects.create(
                room_number=f"E{i+1:02d}", room_type=self.rt_executive,
                floor=7 + i // 3, status="available",
            )
            self.rooms_executive.append(room)
        # Standard has 3 rooms, leave them unbooked
        self.rooms_standard = []
        for i in range(3):
            room = Room.objects.create(
                room_number=f"S{i+1:02d}", room_type=self.rt_standard,
                floor=1 + i, status="available",
            )
            self.rooms_standard.append(room)
        self.demo_check_in = date(2026, 7, 10)
        self.demo_check_out = date(2026, 7, 15)
        self.client.login(username="demo_guest", password="test123")

    def _block_all_rooms(self, rooms, room_type):
        """Helper: create confirmed reservations on all given rooms."""
        for room in rooms:
            RoomReservation.objects.create(
                guest=self.guest, room_type=room_type, room=room,
                check_in=self.demo_check_in, check_out=self.demo_check_out,
                number_of_guests=1, status="confirmed",
                total_price=room_type.price_per_night * 5,
            )

    def test_blocked_type_shows_zero_availability(self):
        self._block_all_rooms(self.rooms_presidential, self.rt_presidential)
        url = reverse("hotel:start_reservation")
        response = self.client.get(
            url + f"?room_type={self.rt_presidential.id}&check_in=2026-07-10&check_out=2026-07-15"
        )
        avail = response.context["room_type_availability"]
        self.assertEqual(avail[self.rt_presidential.id]["available"], 0)
        self.assertEqual(avail[self.rt_presidential.id]["total"], 6)

    def test_guest_cannot_book_blocked_type(self):
        self._block_all_rooms(self.rooms_presidential, self.rt_presidential)
        response = self.client.post(reverse("hotel:start_reservation"), {
            "room_type": self.rt_presidential.id,
            "check_in": "2026-07-10",
            "check_out": "2026-07-15",
            "guests": 1,
        })
        self.assertRedirects(response, reverse("hotel:start_reservation"))
        self.assertIsNone(self.client.session.get("reservation_data"))

    def test_guest_can_book_available_type(self):
        # Standard City Room has no blocking reservations
        response = self.client.post(reverse("hotel:start_reservation"), {
            "room_type": self.rt_standard.id,
            "check_in": "2026-07-10",
            "check_out": "2026-07-15",
            "guests": 1,
        })
        self.assertRedirects(response, reverse("hotel:confirm_reservation"))
        self.assertIsNotNone(self.client.session.get("reservation_data"))
        self.assertEqual(
            self.client.session["reservation_data"]["room_type_id"],
            self.rt_standard.id,
        )

    def test_cancelled_does_not_block_availability(self):
        # Book all rooms with cancelled status — should still show as available
        for room in self.rooms_presidential:
            RoomReservation.objects.create(
                guest=self.guest, room_type=self.rt_presidential, room=room,
                check_in=self.demo_check_in, check_out=self.demo_check_out,
                number_of_guests=1, status="cancelled",
                total_price=self.rt_presidential.price_per_night * 5,
            )
        url = reverse("hotel:start_reservation")
        response = self.client.get(
            url + f"?room_type={self.rt_presidential.id}&check_in=2026-07-10&check_out=2026-07-15"
        )
        avail = response.context["room_type_availability"]
        self.assertEqual(avail[self.rt_presidential.id]["available"], 6)

    def test_completed_does_not_block_availability(self):
        # Completed reservations after checkout should not block
        for room in self.rooms_presidential:
            RoomReservation.objects.create(
                guest=self.guest, room_type=self.rt_presidential, room=room,
                check_in=date(2026, 6, 1), check_out=date(2026, 6, 5),
                number_of_guests=1, status="completed",
                total_price=self.rt_presidential.price_per_night * 4,
            )
        url = reverse("hotel:start_reservation")
        response = self.client.get(
            url + f"?room_type={self.rt_presidential.id}&check_in=2026-07-10&check_out=2026-07-15"
        )
        avail = response.context["room_type_availability"]
        self.assertEqual(avail[self.rt_presidential.id]["available"], 6)


class CancelReservationTests(TestCase):
    def setUp(self):
        self.guest = User.objects.create_user(
            username="cancel_guest", password="test123", role="guest"
        )
        self.staff = User.objects.create_user(
            username="cancel_staff", password="test123", role="staff"
        )
        self.room_type = RoomType.objects.create(
            name="Cancel Room", description="Test",
            price_per_night=Decimal("150"), capacity=2,
        )
        self.room = Room.objects.create(
            room_number="C01", room_type=self.room_type, floor=1,
        )

    def _create_future_reservation(self, days_until_checkin=7):
        check_in = timezone.now().date() + timedelta(days=days_until_checkin)
        check_out = check_in + timedelta(days=2)
        return RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=check_in, check_out=check_out,
            number_of_guests=1, status="confirmed",
            total_price=self.room_type.price_per_night * 2,
        )

    def test_guest_can_cancel_reservation_7_days_before(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=7)
        response = self.client.post(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertRedirects(response, reverse("hotel:my_room_reservations"))
        res.refresh_from_db()
        self.assertEqual(res.status, "cancelled")

    def test_guest_cannot_cancel_within_7_days(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=6)
        response = self.client.post(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertRedirects(
            response, reverse("hotel:my_room_reservation_detail", args=[res.id])
        )
        res.refresh_from_db()
        self.assertNotEqual(res.status, "cancelled")

    def test_guest_cannot_cancel_already_cancelled_reservation(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=14)
        res.status = "cancelled"
        res.save()
        response = self.client.post(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertRedirects(
            response, reverse("hotel:my_room_reservation_detail", args=[res.id])
        )
        res.refresh_from_db()
        self.assertEqual(res.status, "cancelled")

    def test_guest_cannot_cancel_others_reservation(self):
        other = User.objects.create_user(
            username="other_guest", password="test123", role="guest"
        )
        self.client.login(username="cancel_guest", password="test123")
        res = RoomReservation.objects.create(
            guest=other, room_type=self.room_type,
            check_in=timezone.now().date() + timedelta(days=14),
            check_out=timezone.now().date() + timedelta(days=16),
            number_of_guests=1, status="confirmed",
        )
        response = self.client.post(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_non_guest_cannot_cancel(self):
        self.client.login(username="cancel_staff", password="test123")
        res = self._create_future_reservation(days_until_checkin=14)
        response = self.client.post(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertEqual(response.status_code, 302)
        # Not allowed — should be redirected away
        self.assertNotEqual(response.url, reverse("hotel:my_room_reservations"))

    def test_get_request_redirects_to_detail(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=14)
        response = self.client.get(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertRedirects(
            response, reverse("hotel:my_room_reservation_detail", args=[res.id])
        )

    def test_cancel_frees_the_room(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=14)
        room = res.room
        response = self.client.post(
            reverse("hotel:cancel_reservation", args=[res.id])
        )
        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        self.assertEqual(room.status, "available")

    def test_detail_view_shows_cancel_button_when_allowed(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=10)
        response = self.client.get(
            reverse("hotel:my_room_reservation_detail", args=[res.id])
        )
        self.assertTrue(response.context["can_cancel"])
        self.assertContains(response, "Cancel Reservation")

    def test_detail_view_hides_cancel_button_when_too_soon(self):
        self.client.login(username="cancel_guest", password="test123")
        res = self._create_future_reservation(days_until_checkin=3)
        response = self.client.get(
            reverse("hotel:my_room_reservation_detail", args=[res.id])
        )
        self.assertFalse(response.context["can_cancel"])


class StaffRoomVisibilityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="vis_staff", password="test123", role="staff"
        )
        self.guest = User.objects.create_user(
            username="vis_guest", password="test123", role="guest"
        )
        self.room_type = RoomType.objects.create(
            name="Vis Room", description="Test",
            price_per_night=Decimal("100"), capacity=2,
        )
        self.room = Room.objects.create(
            room_number="V01", room_type=self.room_type, floor=1,
        )
        self.ticket = Ticket.objects.create(
            guest=self.guest, assigned_staff=self.staff,
            title="Staff room test", description="Test",
            category="maintenance",
        )

    def test_ticket_list_shows_room_from_active_reservation(self):
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=date(2035, 6, 1), check_out=date(2035, 6, 3),
            number_of_guests=1, status="confirmed",
        )
        self.client.login(username="vis_staff", password="test123")
        response = self.client.get(reverse("hotel:staff_tickets"))
        self.assertEqual(response.status_code, 200)
        ticket = response.context["tickets"][0]
        self.assertEqual(ticket.guest_room_display, "V01")

    def test_ticket_list_shows_na_when_no_room(self):
        self.client.login(username="vis_staff", password="test123")
        response = self.client.get(reverse("hotel:staff_tickets"))
        self.assertEqual(response.status_code, 200)
        ticket = response.context["tickets"][0]
        self.assertFalse(hasattr(ticket, "guest_room_display"))

    def test_ticket_detail_shows_room_from_active_reservation(self):
        RoomReservation.objects.create(
            guest=self.guest, room_type=self.room_type, room=self.room,
            check_in=date(2035, 6, 1), check_out=date(2035, 6, 3),
            number_of_guests=1, status="confirmed",
        )
        self.client.login(username="vis_staff", password="test123")
        response = self.client.get(
            reverse("hotel:staff_ticket_detail", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["guest_room"])
        self.assertEqual(response.context["guest_room"].room_number, "V01")

    def test_ticket_detail_shows_na_when_no_room(self):
        self.client.login(username="vis_staff", password="test123")
        response = self.client.get(
            reverse("hotel:staff_ticket_detail", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["guest_room"])

    def test_ticket_with_explicit_room_shows_it(self):
        other_room = Room.objects.create(
            room_number="V02", room_type=self.room_type, floor=1,
        )
        self.ticket.room = other_room
        self.ticket.save()
        self.client.login(username="vis_staff", password="test123")
        response = self.client.get(
            reverse("hotel:staff_ticket_detail", args=[self.ticket.id])
        )
        self.assertContains(response, "V02")
        # guest_room fallback should be None since ticket.room is set
        self.assertIsNone(response.context["guest_room"])
