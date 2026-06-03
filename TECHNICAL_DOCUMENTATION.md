# Technical Documentation

## Architecture

The Seaside Hotel Management System follows Django's Model-View-Template (MVT) architecture with a single app (`hotel`) inside the `smart_hotel` project.

### Project Structure

```
smart_hotel/              # Django project configuration
├── smart_hotel/          # Project settings, URLs, WSGI
│   ├── settings.py       # Django configuration
│   ├── urls.py           # Root URL routing
│   └── wsgi.py           # WSGI application
├── hotel/                # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View logic (FBVs + DRF API views)
│   ├── forms.py          # Form definitions
│   ├── urls.py           # App URL routing
│   ├── decorators.py     # Role-based access decorators
│   ├── context_processors.py  # Template context
│   ├── admin.py          # Django Admin registration
│   ├── tests.py          # Unit tests
│   ├── management/commands/seed.py  # Sample data seeder
│   ├── templates/        # HTML templates
│   └── static/           # CSS, JS, images
└── media/                # User-uploaded content
```

## Models & Relationships

### User (Custom User Model)
- Inherits `AbstractUser` from Django
- Fields: `role` (guest/staff/manager), `phone_number`, `profile_picture`, `created_at`
- Methods: `is_guest()`, `is_manager()` (role check helpers)
- Uses Django's built-in `is_staff` field for admin access

### RoomType
- Fields: `name`, `description`, `price_per_night`, `capacity`, `image`, `amenities`, `is_active`
- Related to: Room (one-to-many)

### Room
- Fields: `room_number`, `room_type` (FK), `floor`, `status` (available/occupied/maintenance/inactive), `is_active`
- Related to: RoomType (many-to-one), RoomReservation (one-to-many), Ticket (one-to-many)

### RoomReservation
- Fields: `guest` (FK User), `room_type` (FK), `room` (FK nullable), `check_in`, `check_out`, `number_of_guests`, `status` (pending/confirmed/cancelled/completed), `total_price`
- Validates: check_out after check_in, capacity limits, no overlapping dates

### CommonArea
- Fields: `name`, `description`, `capacity`, `location`, `image`, `opening_time`, `closing_time`, `is_active`

### CommonAreaReservation
- Fields: `guest` (FK), `common_area` (FK), `reservation_date`, `start_time`, `end_time`, `number_of_people`, `status`
- Validates: time ordering, capacity, operating hours, no overlaps

### Announcement
- Fields: `title`, `content`, `created_by` (FK Manager), `target_audience` (all/guests/staff), `is_active`

### Ticket
- Fields: `guest` (FK), `assigned_staff` (FK nullable), `title`, `description`, `category` (maintenance/complaint/housekeeping/technical/other), `priority` (low/medium/high/urgent), `status` (open/assigned/in_progress/resolved/closed), `room` (FK nullable)

### TicketNote
- Fields: `ticket` (FK), `user` (FK), `note`, `created_at`
- Provides chronological log of ticket activity

### Entity Relationships

```
User (1) ──< (N) RoomReservation
User (1) ──< (N) CommonAreaReservation
User (1) ──< (N) Ticket (as guest)
User (1) ──< (N) Ticket (as assigned_staff)
User (1) ──< (N) Announcement (as created_by)
User (1) ──< (N) TicketNote
RoomType (1) ──< (N) Room
RoomType (1) ──< (N) RoomReservation
Room (1) ──< (N) RoomReservation
Room (1) ──< (N) Ticket
CommonArea (1) ──< (N) CommonAreaReservation
Ticket (1) ──< (N) TicketNote
```

## Authorization Logic

Authorization is implemented through custom decorators in `decorators.py`:

- `@guest_required` - Only guest role can access
- `@staff_required` - Only staff role can access
- `@manager_required` - Only manager role can access
- `@role_required(['guest', 'staff'])` - Custom role combination

The decorator chain:
1. Checks if user is authenticated
2. Checks if user's role matches the allowed roles
3. Redirects to appropriate dashboard or login page on failure

Role checks are also done in templates via `user.is_guest`, `user.is_manager`, and Django's built-in `user.is_staff`.

## Reservation Flow

1. **Browse**: Visitor views room types on public pages
2. **Select**: Visitor selects a room type, check-in/out dates on `/reserve/`
3. **Session Storage**: Room type ID, dates, and guest count stored in session
4. **Auth Check**: If not logged in, redirected to login/register with reservation data preserved
5. **Confirmation**: Logged-in user sees price summary on `/reserve/confirm/`
6. **Complete**: On confirmation, RoomReservation created with status "confirmed"
7. **Cleanup**: Session data cleared after successful reservation

This flow ensures a seamless booking experience while requiring authentication only at the final step.

## Ticket Assignment Flow

1. **Guest creates ticket** → Status: "open", no assigned staff
2. **Manager views ticket** in Ticket Management dashboard
3. **Manager assigns staff** via `Assign / Update` form on ticket detail
4. System auto-updates status from "open" to "assigned" when staff is assigned
5. **Staff views ticket** in their dashboard (only their assigned tickets)
6. **Staff updates status** via dropdown: "assigned" → "in_progress" → "resolved"
7. **Staff adds internal notes** that are visible to managers and other staff
8. **Manager can override** status or reassign at any time

## Theme System

- Theme preference stored in cookie (`theme`) with 1-year expiry
- Toggle link toggles between `dark` and `light` values
- `context_processors.py` exposes `theme` variable to all templates
- CSS uses CSS custom properties (`--bg-body`, `--text-color`, etc.)
- `data-bs-theme` attribute on `<html>` enables Bootstrap 5 dark mode
- All theme variables defined for both light and dark variants
- Cookie-based (persists across sessions without login requirement)

## Design Choices

### Why Function-Based Views?
The project uses function-based views for simplicity and clarity. Each view is a straightforward Python function that:
- Handles GET and POST in a single function
- Contains clear logic flow without class boilerplate
- Is easy to test and maintain

### Why Custom User Model?
- Adds `role` field directly on the User model
- Eliminates need for separate Profile model
- Simplifies permission checks (`user.role == 'manager'`)
- Future-proof for adding more fields

### Why Session for Reservation Flow?
The session-based approach allows visitors to browse and select without login, then authenticate at the last step. This:
- Reduces friction in the booking process
- Preserves user selections during login redirect
- Avoids complex URL parameter passing

### Why Bootstrap 5?
- Rapid development of responsive layouts
- Built-in dark mode support via `data-bs-theme`
- Extensive component library (cards, tables, forms, modals)
- Familiar to most developers

## Performance Optimizations

- `select_related()` used for ForeignKey relationships in list views
- `Prefetch` and `prefetch_related` for reverse relations
- Pagination on all list views (10-15 items per page)
- Filtered querysets at database level (not in Python)
- Template-level caching via Django template engine

## Security Measures

- CSRF protection on all forms
- Role-based decorators prevent unauthorized access
- `get_object_or_404` ensures users can only access their own data
- Password validation via Django's built-in validators
- Session-based authentication
- No hardcoded secrets in code (using `.env`)
