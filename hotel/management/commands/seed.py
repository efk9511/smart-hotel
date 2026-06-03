from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from hotel.models import (
    Announcement, CommonArea, CommonAreaReservation, HotelOffer, Room,
    RoomReservation, RoomType, Ticket, TicketNote, User,
)


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        #  Create Users 
        manager, created = User.objects.get_or_create(
            username="manager",
        )
        manager.email = "manager@seasidehotel.com"
        manager.first_name = "John"
        manager.last_name = "Smith"
        manager.role = "manager"
        manager.phone_number = "+1-555-0100"
        manager.is_superuser = True
        manager.set_password("Manager123!")
        manager.save()

        staff1, _ = User.objects.get_or_create(
            username="staff1",
            defaults={
                "email": "staff1@seasidehotel.com",
                "first_name": "Alice",
                "last_name": "Johnson",
                "role": "staff",
                "phone_number": "+1-555-0101",
            },
        )
        staff1.set_password("Staff123!")
        staff1.save()

        staff2, _ = User.objects.get_or_create(
            username="staff2",
            defaults={
                "email": "staff2@seasidehotel.com",
                "first_name": "Bob",
                "last_name": "Williams",
                "role": "staff",
                "phone_number": "+1-555-0102",
            },
        )
        staff2.set_password("Staff123!")
        staff2.save()

        guest1, _ = User.objects.get_or_create(
            username="guest1",
            defaults={
                "email": "guest1@email.com",
                "first_name": "Emma",
                "last_name": "Brown",
                "role": "guest",
                "phone_number": "+1-555-0103",
            },
        )
        guest1.set_password("Guest123!")
        guest1.save()

        guest2, _ = User.objects.get_or_create(
            username="guest2",
            defaults={
                "email": "guest2@email.com",
                "first_name": "James",
                "last_name": "Davis",
                "role": "guest",
                "phone_number": "+1-555-0104",
            },
        )
        guest2.set_password("Guest123!")
        guest2.save()

        guest3, _ = User.objects.get_or_create(
            username="guest3",
            defaults={
                "email": "guest3@email.com",
                "first_name": "Sarah",
                "last_name": "Miller",
                "role": "guest",
                "phone_number": "+1-555-0105",
            },
        )
        guest3.set_password("Guest123!")
        guest3.save()

        #  Create/Update Admin Superuser 
        admin_user, created = User.objects.get_or_create(
            username="admin",
        )
        admin_user.email = "admin@example.com"
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.role = "manager"
        admin_user.set_password("admin")
        admin_user.save()

        self.stdout.write(self.style.SUCCESS("  [OK] Users created"))

        #  Create Room Types (Seaside Concept) 
        room_image_map = {
            "Standard City Room": "images/rooms/standard_city_room.png",
            "Deluxe Sea View Room": "images/rooms/deluxe_sea_view_room.png",
            "Family Sea View Suite": "images/rooms/family_sea_view_suite.png",
            "Executive Business Room": "images/rooms/executive_business_room.png",
            "Presidential Sea View Suite": "images/rooms/presidential_sea_view_suite.png",
        }

        rt_standard, _ = RoomType.objects.get_or_create(
            name="Standard City Room",
            defaults={
                "description": "Comfortable room with a queen bed and city views. Features a work desk, mini-bar, smart TV, and modern bathroom. Ideal for business travelers and couples.",
                "price_per_night": Decimal("180.00"),
                "capacity": 2,
                "amenities": "Queen Bed,City View,Work Desk,Mini-Bar,Free Wi-Fi,Smart TV,Air Conditioning,Safe",
                "is_active": True,
                "static_image": room_image_map["Standard City Room"],
            },
        )

        rt_deluxe_sea, _ = RoomType.objects.get_or_create(
            name="Deluxe Sea View Room",
            defaults={
                "description": "Elegant room with a king-size bed and stunning direct sea views through floor-to-ceiling windows. Enjoy the ocean breeze from your private balcony. Features premium bedding, a marble bathroom with rain shower, and Nespresso machine.",
                "price_per_night": Decimal("350.00"),
                "capacity": 2,
                "amenities": "King Bed,Sea View,Private Balcony,Marble Bathroom,Rain Shower,Nespresso,Free Wi-Fi,Smart TV,Air Conditioning,Mini-Bar",
                "is_active": True,
                "static_image": room_image_map["Deluxe Sea View Room"],
            },
        )

        rt_family_suite, _ = RoomType.objects.get_or_create(
            name="Family Sea View Suite",
            defaults={
                "description": "Spacious family suite with two queen beds, a separate living area, and panoramic sea views. Children stay and eat free with meal plans. Includes a kitchenette, dining area, and premium family-friendly amenities.",
                "price_per_night": Decimal("450.00"),
                "capacity": 4,
                "amenities": "Two Queen Beds,Sea View,Living Area,Kitchenette,Dining Area,Free Wi-Fi,Smart TV,Air Conditioning,Mini-Fridge,Children Welcome",
                "is_active": True,
                "static_image": room_image_map["Family Sea View Suite"],
            },
        )

        rt_executive, _ = RoomType.objects.get_or_create(
            name="Executive Business Room",
            defaults={
                "description": "Designed for the discerning business traveler with a king bed, dedicated workspace, ergonomic chair, and high-speed fiber internet. Access to the Executive Lounge with complimentary breakfast and evening canapés.",
                "price_per_night": Decimal("400.00"),
                "capacity": 2,
                "amenities": "King Bed,Work Desk,Ergonomic Chair,Fiber Internet,Executive Lounge Access,Free Wi-Fi,Smart TV,Air Conditioning,Mini-Bar,Printer Access",
                "is_active": True,
                "static_image": room_image_map["Executive Business Room"],
            },
        )

        rt_presidential, _ = RoomType.objects.get_or_create(
            name="Presidential Sea View Suite",
            defaults={
                "description": "Our flagship suite on the top floor with 360-degree sea and city views. Features a grand living room, private dining area, personal butler service, outdoor terrace with jacuzzi, and a master bedroom with walk-in closet. The ultimate coastal luxury experience.",
                "price_per_night": Decimal("950.00"),
                "capacity": 4,
                "amenities": "King Bed,Panoramic Sea View,Private Terrace,Jacuzzi,Butler Service,Living Room,Dining Area,Walk-In Closet,Free Wi-Fi,Smart TV,Air Conditioning,Kitchenette",
                "is_active": True,
                "static_image": room_image_map["Presidential Sea View Suite"],
            },
        )

        # Ensure static_image is set even if records already existed
        for name, path in room_image_map.items():
            RoomType.objects.filter(name=name).update(static_image=path)

        self.stdout.write(self.style.SUCCESS("  [OK] Room types created"))

        #  Create Rooms (12 floors) 
        floor_map = {
            1: rt_standard,
            2: rt_standard,
            3: rt_deluxe_sea,
            4: rt_deluxe_sea,
            5: rt_family_suite,
            6: rt_family_suite,
            7: rt_executive,
            8: rt_executive,
            9: rt_deluxe_sea,
            10: rt_deluxe_sea,
            11: rt_presidential,
            12: rt_presidential,
        }
        for floor in range(1, 13):
            rtype = floor_map[floor]
            for suffix in ["01", "02", "03"]:
                room_num = f"{floor}{suffix}"
                status = "available" if suffix != "03" or floor != 4 else "maintenance"
                Room.objects.get_or_create(
                    room_number=room_num,
                    defaults={
                        "room_type": rtype,
                        "floor": floor,
                        "status": status,
                        "is_active": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("  [OK] Rooms created"))

        #  Create Common Areas (Seaside) 
        areas = [
            ("Infinity Pool", "Stunning infinity pool overlooking the sea. Heated year-round with sun loungers, poolside service, and a separate children's section.", 80, "Ground Floor - Outdoor", time(7, 0), time(21, 0)),
            ("Spa & Wellness", "Full-service spa offering massages, facials, a Turkish hammam, sauna, steam rooms, and a relaxation lounge with sea views.", 25, "2nd Floor", time(8, 0), time(22, 0)),
            ("Fitness Center", "Modern gym with floor-to-ceiling sea views. Equipped with Life Fitness cardio machines, free weights, and a yoga studio.", 35, "3rd Floor", time(6, 0), time(23, 0)),
            ("Cinema Room", "Private cinema with 4K laser projection, Dolby Atmos surround sound, and leather recliners. Screens daily movies and sports events.", 20, "4th Floor", time(10, 0), time(23, 0)),
            ("Conference Hall", "State-of-the-art conference hall for meetings, seminars, and events. Features a stage, 4K display, sound system, and catering kitchen.", 120, "Ground Floor - East Wing", time(7, 0), time(20, 0)),
            ("Rooftop Lounge", "Open-air rooftop bar and lounge with 360-degree panoramic sea and sunset views. Handcrafted cocktails, live acoustic music on weekends, and a tapas menu.", 70, "Rooftop", time(16, 0), time(1, 0)),
        ]
        for name, desc, cap, loc, open_t, close_t in areas:
            CommonArea.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "capacity": cap,
                    "location": loc,
                    "opening_time": open_t,
                    "closing_time": close_t,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("  [OK] Common areas created"))

        #  Create Hotel Offers 
        rooftop = CommonArea.objects.get(name="Rooftop Lounge")
        pool = CommonArea.objects.get(name="Infinity Pool")
        spa = CommonArea.objects.get(name="Spa & Wellness")
        gym = CommonArea.objects.get(name="Fitness Center")
        cinema = CommonArea.objects.get(name="Cinema Room")
        conference = CommonArea.objects.get(name="Conference Hall")

        offer_image_map = {
            "Executive Conference Package": "images/offers/conference_package.png",
            "Sea View Breakfast at Azure Restaurant": "images/offers/sea_view_breakfast.png",
            "Private Cinema Night": "images/offers/private_cinema.png",
            "Sunset Rooftop Lounge Evening": "images/offers/rooftop_lounge.png",
            "Kids Club Creative Workshop": "images/offers/kids_club.png",
            "Fitness Center Personal Training": "images/offers/fitness_training.png",
            "Yoga at Sunrise": "images/offers/yoga_sunrise.png",
            "Infinity Pool Morning Session": "images/offers/infinity_pool.png",
            "Couples Spa Retreat": "images/offers/couples_spa_retreat.png",
            "Spa & Wellness Relax Package": "images/offers/spa_wellness.png",
        }

        offers_data = [
            ("Sunset Rooftop Lounge Evening", "Enjoy breathtaking sunset views from our rooftop lounge with handcrafted cocktails, live acoustic music, and a selection of gourmet tapas. The perfect evening experience.", "entertainment", rooftop, time(17, 0), time(23, 0), None, True),
            ("Sea View Breakfast at Azure Restaurant", "Start your day with a magnificent breakfast buffet overlooking the Mediterranean. Fresh local ingredients, organic options, and made-to-order omelets.", "dining", None, time(7, 0), time(11, 0), Decimal("25.00"), False),
            ("Infinity Pool Morning Session", "Beat the crowds with an exclusive morning session at our heated infinity pool. Includes poolside towel service, fresh fruit, and infused water.", "pool", pool, time(7, 0), time(10, 0), None, True),
            ("Spa & Wellness Relax Package", "Indulge in our signature 90-minute aromatherapy massage followed by unlimited access to the sauna, steam room, and relaxation lounge with sea views.", "spa", spa, None, None, Decimal("120.00"), False),
            ("Private Cinema Night", "Reserve our private cinema for an unforgettable movie night. Choose from our library of 500+ films or bring your own. Includes popcorn and drinks.", "entertainment", cinema, time(18, 0), time(23, 0), Decimal("50.00"), False),
            ("Executive Conference Package", "Fully equipped conference hall with 4K display, sound system, high-speed WiFi, catering, and dedicated event coordinator. Half-day and full-day rates available.", "business", conference, time(7, 0), time(20, 0), Decimal("300.00"), False),
            ("Fitness Center Personal Training", "Book a one-on-one session with our certified personal trainer. Includes customized workout plan, nutritional advice, and a complimentary protein shake.", "fitness", gym, time(6, 0), time(21, 0), Decimal("45.00"), False),
            ("Kids Club Creative Workshop", "Let your children enjoy creative activities including painting, crafts, and storytelling in a safe, supervised environment. Suitable for ages 4-12.", "family", None, time(10, 0), time(16, 0), None, True),
            ("Yoga at Sunrise", "Join our daily sunrise yoga session on the rooftop terrace overlooking the sea. All levels welcome. Mats and props provided.", "fitness", None, time(6, 30), time(7, 30), None, True),
            ("Couples Spa Retreat", "A romantic spa experience for two including a side-by-side massage, facial treatments, and a glass of champagne in our private couple's suite.", "spa", spa, None, None, Decimal("250.00"), False),
        ]
        for title, desc, otype, area, start_t, end_t, price, free in offers_data:
            defaults = {
                "description": desc,
                "offer_type": otype,
                "common_area": area,
                "start_time": start_t,
                "end_time": end_t,
                "price": price,
                "is_free_for_guests": free,
                "is_active": True,
            }
            if title in offer_image_map:
                defaults["static_image"] = offer_image_map[title]
            HotelOffer.objects.get_or_create(title=title, defaults=defaults)

        # Ensure static_image is set even if offers already existed
        for title, path in offer_image_map.items():
            HotelOffer.objects.filter(title=title).update(static_image=path)

        self.stdout.write(self.style.SUCCESS("  [OK] Hotel offers created"))

        #  Create Reservations 
        today = timezone.now().date()
        RoomReservation.objects.get_or_create(
            guest=guest1,
            room_type=rt_deluxe_sea,
            check_in=today + timedelta(days=2),
            defaults={
                "check_out": today + timedelta(days=5),
                "number_of_guests": 2,
                "status": "confirmed",
                "total_price": rt_deluxe_sea.price_per_night * 3,
            },
        )

        RoomReservation.objects.get_or_create(
            guest=guest2,
            room_type=rt_executive,
            check_in=today + timedelta(days=1),
            defaults={
                "check_out": today + timedelta(days=4),
                "number_of_guests": 1,
                "status": "confirmed",
                "total_price": rt_executive.price_per_night * 3,
            },
        )

        RoomReservation.objects.get_or_create(
            guest=guest3,
            room_type=rt_family_suite,
            check_in=today + timedelta(days=5),
            defaults={
                "check_out": today + timedelta(days=8),
                "number_of_guests": 3,
                "status": "pending",
                "total_price": rt_family_suite.price_per_night * 3,
            },
        )

        # Past completed reservation
        RoomReservation.objects.get_or_create(
            guest=guest1,
            room_type=rt_standard,
            check_in=today - timedelta(days=10),
            defaults={
                "check_out": today - timedelta(days=7),
                "number_of_guests": 1,
                "status": "completed",
                "total_price": rt_standard.price_per_night * 3,
            },
        )

        # Demo: Block all Presidential Sea View Suite rooms for a fixed date range
        # This allows demonstrating that the system prevents booking unavailable types
        demo_check_in = date(2026, 7, 10)
        demo_check_out = date(2026, 7, 15)
        for room in rt_presidential.rooms.filter(is_active=True):
            RoomReservation.objects.get_or_create(
                room=room,
                defaults={
                    "guest": guest1,
                    "room_type": rt_presidential,
                    "check_in": demo_check_in,
                    "check_out": demo_check_out,
                    "number_of_guests": 1,
                    "status": "confirmed",
                    "total_price": rt_presidential.price_per_night * (demo_check_out - demo_check_in).days,
                },
            )

        # Demo: Block all Executive Business Room rooms for the same fixed date range
        for room in rt_executive.rooms.filter(is_active=True):
            RoomReservation.objects.get_or_create(
                room=room,
                defaults={
                    "guest": guest2,
                    "room_type": rt_executive,
                    "check_in": demo_check_in,
                    "check_out": demo_check_out,
                    "number_of_guests": 1,
                    "status": "confirmed",
                    "total_price": rt_executive.price_per_night * (demo_check_out - demo_check_in).days,
                },
            )

        self.stdout.write(self.style.SUCCESS("  [OK] Reservations created"))

        #  Create Common Area Reservations 
        pool = CommonArea.objects.get(name="Infinity Pool")
        spa = CommonArea.objects.get(name="Spa & Wellness")
        gym = CommonArea.objects.get(name="Fitness Center")

        CommonAreaReservation.objects.get_or_create(
            guest=guest1,
            common_area=pool,
            defaults={
                "reservation_date": today + timedelta(days=2),
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "number_of_people": 2,
                "status": "confirmed",
            },
        )

        CommonAreaReservation.objects.get_or_create(
            guest=guest2,
            common_area=spa,
            defaults={
                "reservation_date": today + timedelta(days=3),
                "start_time": time(14, 0),
                "end_time": time(16, 0),
                "number_of_people": 1,
                "status": "confirmed",
            },
        )

        CommonAreaReservation.objects.get_or_create(
            guest=guest3,
            common_area=gym,
            defaults={
                "reservation_date": today + timedelta(days=4),
                "start_time": time(7, 0),
                "end_time": time(8, 30),
                "number_of_people": 2,
                "status": "pending",
            },
        )

        self.stdout.write(self.style.SUCCESS("  [OK] Common area reservations created"))

        #  Create Announcements 
        Announcement.objects.get_or_create(
            title="Welcome to Seaside Hotel",
            defaults={
                "content": "We are delighted to welcome you to Seaside Hotel. Enjoy breathtaking sea views, world-class amenities, and warm coastal hospitality. Our team is committed to making your stay unforgettable.",
                "created_by": manager,
                "target_audience": "all",
                "is_active": True,
            },
        )

        Announcement.objects.get_or_create(
            title="Summer Seascape Package",
            defaults={
                "content": "Book your summer getaway and enjoy a 20% discount on Deluxe Sea View rooms and above! Package includes complimentary breakfast, sunset cocktail at the Rooftop Lounge, and access to the Spa & Wellness center.",
                "created_by": manager,
                "target_audience": "guests",
                "is_active": True,
            },
        )

        Announcement.objects.get_or_create(
            title="Staff Meeting Friday",
            defaults={
                "content": "All staff are required to attend the weekly meeting this Friday at 9 AM in the Conference Hall. Agenda includes summer readiness review and new guest experience initiatives.",
                "created_by": manager,
                "target_audience": "staff",
                "is_active": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("  [OK] Announcements created"))

        #  Create Tickets 
        ticket1, _ = Ticket.objects.get_or_create(
            title="Air conditioning not working",
            guest=guest1,
            defaults={
                "description": "The AC in room 301 is not cooling properly. The room temperature is very uncomfortable even at the lowest setting.",
                "category": "maintenance",
                "priority": "high",
                "status": "assigned",
                "assigned_staff": staff1,
            },
        )

        ticket2, _ = Ticket.objects.get_or_create(
            title="Noisy neighbors",
            guest=guest2,
            defaults={
                "description": "The guests in the next room are being very loud after midnight. Unable to sleep. Would appreciate a quiet room change if possible.",
                "category": "complaint",
                "priority": "medium",
                "status": "assigned",
                "assigned_staff": staff2,
            },
        )

        ticket3, _ = Ticket.objects.get_or_create(
            title="Towels not replaced",
            guest=guest3,
            defaults={
                "description": "Housekeeping did not replace our towels today. We requested fresh towels in the morning. We are in room 502.",
                "category": "housekeeping",
                "priority": "low",
                "status": "in_progress",
                "assigned_staff": staff1,
            },
        )

        ticket4, _ = Ticket.objects.get_or_create(
            title="WiFi connection issues",
            guest=guest1,
            defaults={
                "description": "The WiFi keeps disconnecting every few minutes from the sea-view side of the hotel. Very frustrating when trying to work from the room.",
                "category": "technical",
                "priority": "high",
                "status": "open",
            },
        )

        ticket5, _ = Ticket.objects.get_or_create(
            title="Broken TV remote",
            guest=guest2,
            defaults={
                "description": "The TV remote control in room 702 is not working. Batteries have been replaced but still no response from the TV.",
                "category": "maintenance",
                "priority": "low",
                "status": "resolved",
                "assigned_staff": staff2,
            },
        )

        self.stdout.write(self.style.SUCCESS("  [OK] Tickets created"))

        #  Create Ticket Notes 
        TicketNote.objects.get_or_create(
            ticket=ticket1,
            user=staff1,
            defaults={"note": "Checked the AC unit on floor 3. The compressor appears to be faulty. Need to order a replacement part."},
        )

        TicketNote.objects.get_or_create(
            ticket=ticket1,
            user=staff1,
            defaults={"note": "Part has been ordered. Expected delivery in 2 days. Guest has been offered a portable fan and complimentary breakfast."},
        )

        TicketNote.objects.get_or_create(
            ticket=ticket5,
            user=staff2,
            defaults={"note": "Replaced the remote with a universal remote. Working now. Tested all functions."},
        )

        self.stdout.write(self.style.SUCCESS("  [OK] Ticket notes created"))

        self.stdout.write(self.style.SUCCESS("\n Database seeded successfully!"))
        self.stdout.write("-" * 50)
        self.stdout.write("Demo Accounts:")
        self.stdout.write("  Admin:   admin / admin")
        self.stdout.write("  Manager: manager / Manager123!")
        self.stdout.write("  Staff:   staff1 / Staff123!")
        self.stdout.write("  Staff:   staff2 / Staff123!")
        self.stdout.write("  Guest:   guest1 / Guest123!")
        self.stdout.write("  Guest:   guest2 / Guest123!")
        self.stdout.write("  Guest:   guest3 / Guest123!")
        self.stdout.write("-" * 50)
