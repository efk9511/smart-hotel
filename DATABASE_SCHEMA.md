# Database Schema

## Entity-Relationship Diagram

```
  ┌────────────────────┐
  │       User         │──┐
  │────────────────────│  │  ┌───────────────────────────┐
  │ PK  id             │  │  │     RoomReservation       │
  │     username       │  ├──│───────────────────────────│
  │     password       │  │  │ PK  id                    │
  │     email          │  │  │ FK guest ─────────> User  │
  │     first_name     │  │  │ FK room_type ───> RoomType│
  │     last_name      │  │  │ FK room ────────> Room    │
  │     role           │  │  │     check_in              │
  │     phone_number   │──┤  │     check_out             │
  │     profile_pic    │  │  │     number_of_guests      │
  │     created_at     │  │  │     status                │
  └────────────────────┘  │  │     total_price           │
         │                │  │     created_at            │
         │                │  └───────────────────────────┘
         │                │
         │                │  ┌───────────────────────────┐
         │                │  │   CommonAreaReservation   │
         │                ├──│───────────────────────────│
         │                │  │ PK  id                    │
         │                │  │ FK guest ─────────> User  │
         │                │  │ FK common_area ─> ComArea │
         │                │  │     reservation_date      │
         │                │  │     start_time            │
         │                │  │     end_time              │
         │                │  │     number_of_people      │
         │                │  │     status                │
         │                │  │     created_at            │
         │                │  └───────────────────────────┘
         │                │
         │                │  ┌───────────────────────────┐
         │                │  │         Ticket            │
         │                ├──│───────────────────────────│
         │                │  │ PK  id                    │
         │                │  │ FK guest ─────────> User  │
         │                │  │ FK assigned_staff ─> User │
         │                │  │ FK room ──────────> Room  │
         │                │  │     title                 │
         │                │  │     description           │
         │                │  │     category              │
         │                │  │     priority              │
         │                │  │     status                │
         │                │  │     created_at            │
         │                │  │     updated_at            │
         │                │  └───────────────────────────┘
         │                │
         │                │  ┌───────────────────────────┐
         │                │  │      TicketNote           │
         │                ├──│───────────────────────────│
         │                │  │ PK  id                    │
         │                │  │ FK ticket ───────> Ticket │
         │                │  │ FK user ─────────> User   │
         │                │  │     note                  │
         │                │  │     created_at            │
         │                │  └───────────────────────────┘
         │                │
         │                │  ┌───────────────────────────┐
         │                │  │      Announcement         │
         │                └──│───────────────────────────│
         │                   │ PK  id                    │
         │                   │ FK created_by ────> User  │
         │                   │     title                 │
         │                   │     content               │
         │                   │     target_audience       │
         │                   │     is_active             │
         │                   │     created_at            │
         │                   └───────────────────────────┘
         │
         │  ┌────────────────────┐
         │  │     RoomType       │
         │  │────────────────────│
         │  │ PK  id             │
         │  │     name           │
         │  │     description    │
         │  │     price_per_night│
         │  │     capacity       │
         │  │     image          │
         │  │     static_image   │
         │  │     amenities      │
         │  │     is_active      │
         │  │     created_at     │
         └──│────────────────────│
            └────────┬───────────┘
                     │ 1
                     │
              has many│
                     │
                     │ *
            ┌────────┴───────────┐
            │       Room         │
            │────────────────────│
            │ PK  id             │
            │ FK room_type ──────│
            │     room_number    │
            │     floor          │
            │     status         │
            │     is_active      │
            │     created_at     │
            └────────────────────┘

  ┌────────────────────┐
  │    CommonArea      │
  │────────────────────│
  │ PK  id             │
  │     name           │
  │     description    │
  │     capacity       │
  │     location       │
  │     image          │
  │     opening_time   │
  │     closing_time   │
  │     is_active      │
  │     created_at     │
  └────────┬───────────┘
           │ 1
           │
    has    │
           │ *
  ┌────────┴──────────────────────────┐
  │          HotelOffer               │
  │───────────────────────────────────│
  │ PK  id                            │
  │ FK common_area ─────────> ComArea │
  │     title                         │
  │     description                   │
  │     offer_type                    │
  │     start_date / end_date         │
  │     start_time / end_time         │
  │     price                         │
  │     is_free_for_guests            │
  │     image / static_image          │
  │     is_active                     │
  │     created_at                    │
  └───────────────────────────────────┘

Relationships (summary):
  User    1──* RoomReservation          (guest)
  User    1──* CommonAreaReservation    (guest)
  User    1──* Ticket                   (guest)
  User    1──* Ticket                   (assigned_staff)
  User    1──* TicketNote               (author)
  User    1──* Announcement             (created_by)
  RoomType 1──* Room
  RoomType 1──* RoomReservation
  Room    1──* RoomReservation
  Room    1──* Ticket
  CommonArea 1──* CommonAreaReservation
  CommonArea 1──* HotelOffer
  Ticket  1──* TicketNote
```

## Models

### User

Extends Django's `AbstractUser`. Acts as a polymorphic actor with a `role` field.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `username` | CharField(150) | unique | From AbstractUser |
| `password` | CharField(128) | | Hashed |
| `email` | EmailField(254) | | From AbstractUser |
| `first_name` | CharField(150) | | |
| `last_name` | CharField(150) | | |
| `role` | CharField(10) | choices: guest/staff/manager, db_index | Determines permissions |
| `phone_number` | CharField(20) | blank=True | |
| `profile_picture` | ImageField | null, upload_to="profiles/" | |
| `created_at` | DateTimeField | auto_now_add | |

**Relationships:**
- `room_reservations` — reverse: reservations made by this user (as guest)
- `common_area_reservations` — reverse: common area bookings by this user
- `tickets` — reverse: tickets created by this user (as guest)
- `assigned_tickets` — reverse: tickets assigned to this user (as staff)
- `ticket_notes` — reverse: notes authored by this user
- `announcements` — reverse: announcements created by this user

---

### RoomType

Describes a category of hotel rooms (e.g. "Deluxe Sea View Room").

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `name` | CharField(100) | | e.g. "Presidential Sea View Suite" |
| `description` | TextField | blank=True | |
| `price_per_night` | Decimal(10,2) | MinValueValidator(0.01) | |
| `capacity` | PositiveIntegerField | MinValueValidator(1) | Max guests |
| `image` | ImageField | null, upload_to="room_types/" | |
| `static_image` | CharField(255) | blank=True | Path like `images/rooms/standard_city_room.png` |
| `amenities` | TextField | blank=True | Comma-separated list |
| `is_active` | BooleanField | default=True, db_index | Soft-delete / hide |
| `created_at` | DateTimeField | auto_now_add | |

**Methods:**
- `amenity_list()` — returns parsed list from `amenities` text field
- `get_available_rooms(check_in, check_out)` — returns active rooms not overlapping with pending/confirmed reservations in the date range
- `available_rooms_count(check_in, check_out)` — count of available rooms

**Relationships:**
- `rooms` — one-to-many to Room
- `reservations` — reverse from RoomReservation

---

### Room

A specific physical room.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `room_number` | CharField(10) | unique | e.g. "101" |
| `room_type` | ForeignKey(RoomType) | NOT NULL, CASCADE | |
| `floor` | PositiveIntegerField | MinValueValidator(1) | |
| `status` | CharField(20) | choices: available/occupied/maintenance/inactive, db_index | |
| `is_active` | BooleanField | default=True, db_index | Soft-delete |
| `created_at` | DateTimeField | auto_now_add | |

**Relationships:**
- `room_type` → RoomType (many-to-one)
- `reservations` — reverse from RoomReservation
- `tickets` — reverse from Ticket

---

### RoomReservation

A booking of a room type (and optionally a specific room) by a guest.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `guest` | ForeignKey(User) | CASCADE | `related_name="room_reservations"` |
| `room_type` | ForeignKey(RoomType) | SET_NULL, null | |
| `room` | ForeignKey(Room) | SET_NULL, null, blank | Assigned by manager or auto-assigned |
| `check_in` | DateField | | |
| `check_out` | DateField | | |
| `number_of_guests` | PositiveIntegerField | MinValueValidator(1) | |
| `status` | CharField(20) | choices: pending/confirmed/cancelled/completed, db_index | |
| `total_price` | Decimal(10,2) | null, blank | Auto-calculated on save |
| `created_at` | DateTimeField | auto_now_add | |

**Status flow:** `pending` → `confirmed` → `completed` | `cancelled`

**Validation (clean):**
- check_out must be after check_in
- check_in cannot be in the past
- number_of_guests cannot exceed room_type.capacity
- No overlapping confirmed/pending reservations for the same room

**Methods:**
- `nights()` — returns (check_out - check_in).days
- `save()` auto-calculates total_price if not set

**Cancellation policy:** Allowed via POST to `/guest/reservations/<pk>/cancel/` only when `check_in` is at least 7 days in the future and status is pending or confirmed. On cancellation, the associated room (if any) is freed back to "available".

**Relationships:**
- `guest` → User
- `room_type` → RoomType
- `room` → Room

---

### CommonArea

A bookable hotel amenity (pool, spa, gym, etc.).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `name` | CharField(100) | | e.g. "Infinity Pool" |
| `description` | TextField | blank=True | |
| `capacity` | PositiveIntegerField | | Max people |
| `location` | CharField(200) | blank=True | e.g. "5th Floor" |
| `image` | ImageField | null, upload_to="common_areas/" | |
| `opening_time` | TimeField | default="08:00" | |
| `closing_time` | TimeField | default="22:00" | |
| `is_active` | BooleanField | default=True | |
| `created_at` | DateTimeField | auto_now_add | |

**Relationships:**
- `reservations` — reverse from CommonAreaReservation
- `offers` — reverse from HotelOffer

---

### CommonAreaReservation

A booking of a common area for a specific date/time slot.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `guest` | ForeignKey(User) | CASCADE | `related_name="common_area_reservations"` |
| `common_area` | ForeignKey(CommonArea) | CASCADE | |
| `reservation_date` | DateField | | |
| `start_time` | TimeField | | |
| `end_time` | TimeField | | |
| `number_of_people` | PositiveIntegerField | MinValueValidator(1) | |
| `status` | CharField(20) | choices: pending/confirmed/cancelled, db_index | |
| `created_at` | DateTimeField | auto_now_add | |

**Validation (clean):**
- end_time must be after start_time
- number_of_people cannot exceed common_area.capacity
- start/end time must be within area's opening hours
- No overlapping confirmed/pending reservations for the same area and date

---

### Ticket

A support or maintenance request submitted by a guest.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `guest` | ForeignKey(User) | CASCADE, related_name="tickets" | Creator |
| `assigned_staff` | ForeignKey(User) | SET_NULL, null, blank, related_name="assigned_tickets" | Staff assignee |
| `title` | CharField(200) | | |
| `description` | TextField | | |
| `category` | CharField(20) | choices: maintenance/complaint/housekeeping/technical/other, db_index | |
| `priority` | CharField(10) | choices: low/medium/high/urgent, db_index | |
| `status` | CharField(20) | choices: open/assigned/in_progress/resolved/closed, db_index | |
| `room` | ForeignKey(Room) | SET_NULL, null, blank | Associated room |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |

**Status flow:** `open` → `assigned` → `in_progress` → `resolved` → `closed`

**Staff room visibility:** When a ticket has no explicit room, staff views fall back to the guest's current confirmed reservation's room.

**Relationships:**
- `guest` → User
- `assigned_staff` → User
- `room` → Room
- `notes` — reverse from TicketNote

---

### TicketNote

Internal notes added to a ticket by staff.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `ticket` | ForeignKey(Ticket) | CASCADE, related_name="notes" | |
| `user` | ForeignKey(User) | CASCADE, related_name="ticket_notes" | Author |
| `note` | TextField | | |
| `created_at` | DateTimeField | auto_now_add | |

**Relationships:**
- `ticket` → Ticket
- `user` → User

---

### Announcement

Broadcast messages displayed on the homepage, targeted by audience.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `title` | CharField(200) | | |
| `content` | TextField | | |
| `created_by` | ForeignKey(User) | CASCADE, related_name="announcements" | |
| `target_audience` | CharField(10) | choices: all/guests/staff, db_index | |
| `is_active` | BooleanField | default=True, db_index | |
| `created_at` | DateTimeField | auto_now_add | |

**Relationships:**
- `created_by` → User

---

### HotelOffer

Promotional offers or activities, optionally linked to a common area.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField | PK | |
| `title` | CharField(200) | | |
| `description` | TextField | | |
| `common_area` | ForeignKey(CommonArea) | SET_NULL, null, blank | Associated facility |
| `offer_type` | CharField(20) | choices: dining/pool/spa/fitness/entertainment/business/family/other | |
| `start_date` | DateField | null, blank | |
| `end_date` | DateField | null, blank | |
| `start_time` | TimeField | null, blank | Daily start |
| `end_time` | TimeField | null, blank | Daily end |
| `price` | Decimal(8,2) | null, blank | |
| `is_free_for_guests` | BooleanField | default=True | |
| `image` | ImageField | null, upload_to="offers/" | |
| `static_image` | CharField(255) | blank=True | Path like `images/offers/rooftop_lounge.png` |
| `is_active` | BooleanField | default=True, db_index | |
| `created_at` | DateTimeField | auto_now_add | |

**Relationships:**
- `common_area` → CommonArea

---

## Indexes

| Table | Indexed Columns | Purpose |
|-------|-----------------|---------|
| `users` | `role` | Filter users by role |
| `room_types` | `is_active` | Show only active room types |
| `rooms` | `status`, `is_active` | Availability queries |
| `room_reservations` | `status` | Filter by status |
| `common_area_reservations` | `status` | Filter by status |
| `tickets` | `category`, `priority`, `status` | Search/filter tickets |
| `announcements` | `target_audience`, `is_active` | Audience-targeted display |
| `hotel_offers` | `is_active` | Active offers only |

## Table Names

| Model | DB Table |
|-------|----------|
| User | `users` |
| RoomType | `room_types` |
| Room | `rooms` |
| RoomReservation | `room_reservations` |
| CommonArea | `common_areas` |
| CommonAreaReservation | `common_area_reservations` |
| Ticket | `tickets` |
| TicketNote | `ticket_notes` |
| Announcement | `announcements` |
| HotelOffer | `hotel_offers` |
