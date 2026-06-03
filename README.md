# Seaside Hotel Management System

A comprehensive Django-based hotel management web application with role-based access control, room reservations, common area booking, maintenance ticketing, and administrative dashboards — themed for a modern coastal seaside hotel.

## Features

- **Three user roles**: Guest, Staff, Manager with granular permissions
- **Room Booking**: Browse sea-view room types, select dates, and confirm reservations
- **Auto Room Assignment**: Available rooms are automatically assigned on confirmation
- **Room Availability Blocking**: Demo reservations can be configured to block specific room types for given dates
- **Reservation Cancellation**: Guests can cancel reservations up to 7 days before check-in with a 7-day policy
- **Common Area Reservations**: Book infinity pool, spa, rooftop lounge, cinema, gym, and conference hall
- **Ticket System**: Submit maintenance/concierge tickets with priority levels
- **Staff Room Visibility**: Staff see guest room info from the ticket or the guest's active reservation
- **Staff Assignment**: Managers can assign tickets to specific staff members
- **AJAX Updates**: Real-time ticket status changes without page reload
- **Dark/Light Theme**: Persistent theme toggle saved in localStorage
- **Dashboard Statistics**: Role-specific dashboards with key metrics
- **Search & Filtering**: Find tickets, reservations, and users quickly
- **Pagination**: All list views support pagination
- **Print Support**: Printable reservation confirmation pages
- **Manager Reports**: Revenue and status breakdown reports
- **English-only Interface**: Clean and consistent user experience
- **REST API**: Public endpoints for room types and common areas
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Django Admin**: Available only as superuser backup

## User Roles

| Role | Capabilities |
|------|-------------|
| **Guest** | Register, login, browse rooms, make reservations, cancel reservations (7+ days before check-in), book common areas, create tickets, view own data |
| **Staff** | View assigned tickets (with guest room info), update ticket status, add internal notes |
| **Manager** | Full CRUD on users, rooms, room types, announcements, offers; manage all reservations and tickets; assign rooms to reservations; view reports |

## Tech Stack

- Python 3.13
- Django 6.0
- SQLite (development)
- Bootstrap 5.3 (UI framework)
- Django REST Framework (API)
- Whitenoise (static files)
- python-decouple (environment variables)
- dj-database-url (production database)

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd smart_hotel
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for development)
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed sample data

```bash
python manage.py seed
```

### 7. Collect static files

```bash
python manage.py collectstatic
```

### 8. Run the development server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000 in your browser.

## Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| **Manager** | `manager` | `Manager123!` |
| **Staff** | `staff1` | `Staff123!` |
| **Staff** | `staff2` | `Staff123!` |
| **Guest** | `guest1` | `Guest123!` |
| **Guest** | `guest2` | `Guest123!` |
| **Guest** | `guest3` | `Guest123!` |

## Running Tests

```bash
python manage.py test
```

## API Endpoints

- `GET /api/room-types/` - List all active room types
- `GET /api/common-areas/` - List all active common areas

## Deployment

### Render

1. Push to GitHub
2. Create a new Web Service on Render
3. Set build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Set start command: `gunicorn smart_hotel.wsgi`
5. Add environment variables from `.env.example`

### PythonAnywhere

#### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/smart-hotel.git
git push -u origin main
```

#### 2. Open a PythonAnywhere Bash console and clone

```bash
git clone https://github.com/YOUR_USERNAME/smart-hotel.git
cd smart-hotel
```

#### 3. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if needed (the defaults work for PythonAnywhere)
```

#### 5. Run migrations

```bash
python manage.py migrate
```

#### 6. Seed the database

```bash
python manage.py seed
```

#### 7. Collect static files

```bash
python manage.py collectstatic --noinput
```

#### 8. Configure WSGI

On PythonAnywhere, go to the **Web** tab and:

- Set your source code directory to `/home/YOUR_USERNAME/smart-hotel`
- Set your working directory to `/home/YOUR_USERNAME/smart-hotel`
- Set the **virtual environment** to `/home/YOUR_USERNAME/smart-hotel/venv`
- Edit the WSGI configuration file and replace its contents with:

```python
import os
import sys

path = '/home/YOUR_USERNAME/smart-hotel'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'smart_hotel.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### 9. Configure Static Files

On the **Web** tab, under **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/smart-hotel/staticfiles` |
| `/media/` | `/home/YOUR_USERNAME/smart-hotel/media` |

#### 10. Reload

Click the **Reload** button on the Web tab.

Your app will be live at `https://YOUR_USERNAME.pythonanywhere.com`.

## Directory Structure

```
smart_hotel/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── TECHNICAL_DOCUMENTATION.md
├── smart_hotel/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── hotel/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── decorators.py
│   ├── context_processors.py
│   ├── admin.py
│   ├── tests.py
│   ├── management/commands/seed.py
│   ├── templates/hotel/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── public/
│   │   ├── guest/
│   │   ├── staff/
│   │   ├── manager/
│   │   └── partials/
│   └── static/hotel/
│       ├── css/style.css
│       └── js/main.js
├── static/
└── media/
```

## Static Image Assets

Room images are served from the `static/images/rooms/` directory. Place your image files with these exact filenames:

- `standard_city_room.png`
- `deluxe_sea_view_room.png`
- `family_sea_view_suite.png`
- `executive_business_room.png`
- `presidential_sea_view_suite.png`

Offer images are served from the `static/images/offers/` directory:

- `rooftop_lounge.png`
- `sea_view_breakfast.png`
- `infinity_pool.png`
- `spa_wellness.png`
- `private_cinema.png`
- `conference_package.png`
- `fitness_training.png`
- `kids_club.png`
- `yoga_sunrise.png`
- `couples_spa_retreat.png`
- `default_offer.png`

Default placeholder images (`default_room.png`, `default_offer.png`) are provided so pages do not break if an image is missing. If a specific image file is not found, the browser falls back to the default placeholder automatically.

After adding or updating images, run:

```bash
python manage.py collectstatic
```

## License

MIT
