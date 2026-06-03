from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = "guest", "Guest"
        STAFF = "staff", "Staff"
        MANAGER = "manager", "Manager"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.GUEST, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_guest(self):
        return self.role == self.Role.GUEST

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def is_staff_role(self):
        return self.role == self.Role.STAFF


class RoomType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    image = models.ImageField(upload_to="room_types/", blank=True, null=True)
    static_image = models.CharField(max_length=255, blank=True, help_text="Static image path like images/rooms/standard_city_room.png")
    amenities = models.TextField(blank=True, help_text="Comma-separated list of amenities")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "room_types"

    def __str__(self):
        return f"{self.name} - ${self.price_per_night}/night"

    def amenity_list(self):
        return [a.strip() for a in self.amenities.split(",") if a.strip()]

    def get_available_rooms(self, check_in, check_out):
        rooms = self.rooms.filter(status="available", is_active=True)
        booked = RoomReservation.objects.filter(
            room__room_type=self,
            status__in=["pending", "confirmed"],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).values_list("room_id", flat=True)
        return rooms.exclude(id__in=booked).order_by("floor", "room_number")

    def available_rooms_count(self, check_in=None, check_out=None):
        if check_in and check_out:
            return self.get_available_rooms(check_in, check_out).count()
        return self.rooms.filter(status="available", is_active=True).count()

    def get_unavailable_date_ranges(self, start_date=None, end_date=None, max_days=120):
        from datetime import timedelta
        from collections import defaultdict

        today = timezone.now().date()
        if start_date is None:
            start_date = today
        if end_date is None:
            end_date = start_date + timedelta(days=max_days)

        total_active_rooms = self.rooms.filter(is_active=True).count()
        if total_active_rooms == 0:
            return [(start_date, end_date)]

        reservations = RoomReservation.objects.filter(
            room_type=self,
            status__in=["pending", "confirmed"],
            check_in__lt=end_date,
            check_out__gt=start_date,
        )

        unavailable_rooms_count = self.rooms.filter(
            is_active=True
        ).exclude(status="available").count()

        daily_booked = defaultdict(int)
        for res in reservations:
            res_start = max(res.check_in, start_date)
            res_end = min(res.check_out, end_date)
            d = res_start
            while d < res_end:
                daily_booked[d] += 1
                d += timedelta(days=1)

        unavailable_dates = []
        d = start_date
        while d < end_date:
            if daily_booked.get(d, 0) + unavailable_rooms_count >= total_active_rooms:
                unavailable_dates.append(d)
            d += timedelta(days=1)

        if not unavailable_dates:
            return []

        ranges = []
        range_start = unavailable_dates[0]
        range_end = unavailable_dates[0]

        for d in unavailable_dates[1:]:
            if d == range_end + timedelta(days=1):
                range_end = d
            else:
                ranges.append((range_start, range_end + timedelta(days=1)))
                range_start = d
                range_end = d

        ranges.append((range_start, range_end + timedelta(days=1)))
        return ranges

    def get_calendar_unavailable_dates(self, start_date=None, end_date=None, max_days=120):
        from datetime import timedelta
        from collections import defaultdict

        today = timezone.now().date()
        if start_date is None:
            start_date = today
        if end_date is None:
            end_date = start_date + timedelta(days=max_days)

        total_active_rooms = self.rooms.filter(is_active=True).count()
        if total_active_rooms == 0:
            return [d.isoformat() for d in self._date_range(start_date, end_date)]

        reservations = RoomReservation.objects.filter(
            room_type=self,
            status__in=["pending", "confirmed"],
            check_in__lt=end_date,
            check_out__gt=start_date,
        )

        unavailable_rooms_count = self.rooms.filter(
            is_active=True
        ).exclude(status="available").count()

        daily_booked = defaultdict(int)
        for res in reservations:
            res_start = max(res.check_in, start_date)
            res_end = min(res.check_out, end_date)
            d = res_start
            while d < res_end:
                daily_booked[d] += 1
                d += timedelta(days=1)

        unavailable = []
        d = start_date
        while d < end_date:
            if daily_booked.get(d, 0) + unavailable_rooms_count >= total_active_rooms:
                unavailable.append(d.isoformat())
            d += timedelta(days=1)

        return unavailable

    @staticmethod
    def _date_range(start, end):
        from datetime import timedelta
        dates = []
        d = start
        while d < end:
            dates.append(d)
            d += timedelta(days=1)
        return dates


class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        MAINTENANCE = "maintenance", "Maintenance"
        INACTIVE = "inactive", "Inactive"

    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="rooms")
    floor = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rooms"

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name}) - {self.get_status_display()}"


class RoomReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name="room_reservations")
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")
    check_in = models.DateField()
    check_out = models.DateField()
    number_of_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "room_reservations"

    def __str__(self):
        return f"Reservation #{self.id} - {self.guest.username} - {self.room_type}"

    def clean(self):
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError({"check_out": "Check-out date must be after check-in date."})
        if self.check_in and self.check_in < timezone.now().date():
            raise ValidationError({"check_in": "Check-in date cannot be in the past."})
        if self.room_type and self.number_of_guests and self.number_of_guests > self.room_type.capacity:
            raise ValidationError({"number_of_guests": f"Maximum capacity is {self.room_type.capacity} guests."})
        if self.room and self.status in ["pending", "confirmed"]:
            overlapping = RoomReservation.objects.filter(
                room=self.room,
                status__in=["pending", "confirmed"],
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError("This room is already booked for the selected dates.")

    def save(self, *args, **kwargs):
        if not self.total_price and self.room_type and self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            self.total_price = self.room_type.price_per_night * nights
        super().save(*args, **kwargs)

    def nights(self):
        return (self.check_out - self.check_in).days


class CommonArea(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="common_areas/", blank=True, null=True)
    opening_time = models.TimeField(default="08:00")
    closing_time = models.TimeField(default="22:00")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "common_areas"

    def __str__(self):
        return self.name


class CommonAreaReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name="common_area_reservations")
    common_area = models.ForeignKey(CommonArea, on_delete=models.CASCADE, related_name="reservations")
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    number_of_people = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "common_area_reservations"

    def __str__(self):
        return f"{self.common_area.name} - {self.reservation_date} ({self.start_time}-{self.end_time})"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after start time."})
        if self.common_area and self.number_of_people and self.number_of_people > self.common_area.capacity:
            raise ValidationError({"number_of_people": f"Maximum capacity is {self.common_area.capacity} people."})
        if self.common_area and self.start_time:
            if self.start_time < self.common_area.opening_time:
                raise ValidationError({"start_time": f"Common area opens at {self.common_area.opening_time}."})
            if self.end_time > self.common_area.closing_time:
                raise ValidationError({"end_time": f"Common area closes at {self.common_area.closing_time}."})
        if self.common_area and self.reservation_date and self.start_time and self.end_time:
            overlapping = CommonAreaReservation.objects.filter(
                common_area=self.common_area,
                reservation_date=self.reservation_date,
                status__in=["pending", "confirmed"],
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError("This time slot is already booked for this area.")


class Announcement(models.Model):
    class Target(models.TextChoices):
        ALL = "all", "All"
        GUESTS = "guests", "Guests"
        STAFF = "staff", "Staff"

    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="announcements")
    target_audience = models.CharField(max_length=10, choices=Target.choices, default=Target.ALL, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "announcements"

    def __str__(self):
        return self.title


class Ticket(models.Model):
    class Category(models.TextChoices):
        MAINTENANCE = "maintenance", "Maintenance"
        COMPLAINT = "complaint", "Complaint"
        HOUSEKEEPING = "housekeeping", "Housekeeping"
        TECHNICAL = "technical", "Technical"
        OTHER = "other", "Other"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    assigned_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER, db_index=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tickets"

    def __str__(self):
        return f"#{self.id} {self.title} - {self.get_status_display()}"


class TicketNote(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_notes")
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ticket_notes"
        ordering = ["created_at"]

    def __str__(self):
        return f"Note on #{self.ticket.id} by {self.user.username}"


class HotelOffer(models.Model):
    class OfferType(models.TextChoices):
        DINING = "dining", "Dining"
        POOL = "pool", "Pool"
        SPA = "spa", "Spa & Wellness"
        FITNESS = "fitness", "Fitness"
        ENTERTAINMENT = "entertainment", "Entertainment"
        BUSINESS = "business", "Business"
        FAMILY = "family", "Family"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    description = models.TextField()
    common_area = models.ForeignKey(CommonArea, on_delete=models.SET_NULL, null=True, blank=True, related_name="offers")
    offer_type = models.CharField(max_length=20, choices=OfferType.choices, default=OfferType.OTHER)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_free_for_guests = models.BooleanField(default=True)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    static_image = models.CharField(max_length=255, blank=True, help_text="Static image path like images/offers/rooftop_lounge.png")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hotel_offers"
        ordering = ["offer_type", "title"]

    def __str__(self):
        return self.title
