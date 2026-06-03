from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    User, RoomType, Room, RoomReservation,
    CommonArea, CommonAreaReservation, Announcement,
    HotelOffer, Ticket, TicketNote,
)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone_number = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone_number", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.GUEST
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.setdefault("class", "form-control")


class UserProfileForm(BaseForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "profile_picture"]


class UserCreateForm(BaseForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}), required=True)
    role = forms.ChoiceField(choices=User.Role.choices, widget=forms.Select(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone_number", "role", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserUpdateForm(BaseForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone_number", "role", "profile_picture", "is_active"]


class RoomTypeForm(BaseForm):
    class Meta:
        model = RoomType
        fields = ["name", "description", "price_per_night", "capacity", "image", "amenities", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class RoomForm(BaseForm):
    class Meta:
        model = Room
        fields = ["room_number", "room_type", "floor", "status", "is_active"]


class RoomReservationForm(BaseForm):
    class Meta:
        model = RoomReservation
        fields = ["room_type", "check_in", "check_out", "number_of_guests"]
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "check_out": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room_type"].queryset = RoomType.objects.filter(is_active=True)
        self.fields["room_type"].empty_label = "Select Room Type"

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")
        room_type = cleaned_data.get("room_type")
        number_of_guests = cleaned_data.get("number_of_guests")

        if check_in and check_out:
            if check_out <= check_in:
                raise ValidationError("Check-out date must be after check-in date.")
            if check_in < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past.")
            nights = (check_out - check_in).days
            if nights < 1:
                raise ValidationError("Minimum stay is 1 night.")

        if room_type and number_of_guests and number_of_guests > room_type.capacity:
            raise ValidationError(f"Maximum capacity for {room_type.name} is {room_type.capacity} guests.")

        return cleaned_data


class CommonAreaReservationForm(BaseForm):
    class Meta:
        model = CommonAreaReservation
        fields = ["common_area", "reservation_date", "start_time", "end_time", "number_of_people"]
        widgets = {
            "reservation_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["common_area"].queryset = CommonArea.objects.filter(is_active=True)
        self.fields["common_area"].empty_label = "Select Common Area"

    def clean(self):
        cleaned_data = super().clean()
        common_area = cleaned_data.get("common_area")
        reservation_date = cleaned_data.get("reservation_date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        number_of_people = cleaned_data.get("number_of_people")

        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time.")

        if common_area and number_of_people and number_of_people > common_area.capacity:
            raise ValidationError(f"Maximum capacity is {common_area.capacity} people.")

        if common_area and start_time and end_time:
            if start_time < common_area.opening_time:
                raise ValidationError(f"Area opens at {common_area.opening_time}.")
            if end_time > common_area.closing_time:
                raise ValidationError(f"Area closes at {common_area.closing_time}.")

        if common_area and reservation_date and start_time and end_time:
            overlapping = CommonAreaReservation.objects.filter(
                common_area=common_area,
                reservation_date=reservation_date,
                status__in=["pending", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if overlapping.exists():
                raise ValidationError("This time slot is already booked.")

        if reservation_date and reservation_date < timezone.now().date():
            raise ValidationError("Reservation date cannot be in the past.")

        return cleaned_data


class TicketForm(BaseForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority", "room"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.filter(is_active=True, status="available")
        self.fields["room"].required = False
        self.fields["room"].empty_label = "No specific room"


class TicketNoteForm(BaseForm):
    class Meta:
        model = TicketNote
        fields = ["note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Add an internal note...", "class": "form-control"}),
        }


class AnnouncementForm(BaseForm):
    class Meta:
        model = Announcement
        fields = ["title", "content", "target_audience", "is_active"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
        }


class TicketAssignForm(BaseForm):
    class Meta:
        model = Ticket
        fields = ["assigned_staff", "priority"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_staff"].queryset = User.objects.filter(role=User.Role.STAFF, is_active=True)
        self.fields["assigned_staff"].required = False
        self.fields["assigned_staff"].empty_label = "--- Select Staff ---"


class TicketStatusForm(BaseForm):
    class Meta:
        model = Ticket
        fields = ["status"]


class RoomAssignForm(forms.Form):
    room = forms.ModelChoiceField(queryset=Room.objects.none(), required=False, empty_label="--- No room assigned ---")

    def __init__(self, *args, **kwargs):
        reservation = kwargs.pop("reservation", None)
        super().__init__(*args, **kwargs)
        if reservation and reservation.room_type:
            booked_ids = RoomReservation.objects.filter(
                room_type=reservation.room_type,
                status__in=["pending", "confirmed"],
                check_in__lt=reservation.check_out,
                check_out__gt=reservation.check_in,
            ).exclude(pk=reservation.pk if reservation.pk else None).values_list("room_id", flat=True)
            available = Room.objects.filter(
                room_type=reservation.room_type,
                is_active=True,
            ).exclude(status="inactive").exclude(
                id__in=booked_ids
            )
            self.fields["room"].queryset = available
            if reservation.room:
                self.fields["room"].initial = reservation.room


class HotelOfferForm(BaseForm):
    class Meta:
        model = HotelOffer
        fields = ["title", "description", "common_area", "offer_type", "start_date", "end_date", "start_time", "end_time", "price", "is_free_for_guests", "image", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }
