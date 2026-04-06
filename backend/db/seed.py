import sys
import os
from datetime import date

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.db.database import Base, engine, SessionLocal
from backend.db.models import Hotel, RoomType, Booking


def seed(force: bool = False):
    """
    Creates all tables and fills with realistic hotel + room types + bookings.
    Pass force=True to wipe and re-seed.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created / verified")

    db = SessionLocal()

    try:
        if db.query(Hotel).count() > 0:
            if not force:
                print("⚠️  Already seeded. Run with force=True to re-seed.")
                print(f"   Hotels: {db.query(Hotel).count()} | "
                      f"Room types: {db.query(RoomType).count()} | "
                      f"Bookings: {db.query(Booking).count()}")
                return
            # Wipe existing data
            db.query(Booking).delete()
            db.query(RoomType).delete()
            db.query(Hotel).delete()
            db.commit()
            print("🗑️  Existing data cleared")

        # ── Hotels ────────────────────────────────────────────────────────────
        hotels = [
            # ── London (5 hotels) ──────────────────────────────────────────────
            Hotel(
                name="The Savoy London",
                location="London",
                amenities="WiFi, Spa, Pool, Gym, Restaurant, Room Service, Valet Parking",
                rating=4.9,
            ),
            Hotel(
                name="Claridge's",
                location="London",
                amenities="WiFi, Fine Dining, Bar, Concierge, Butler Service",
                rating=4.8,
            ),
            Hotel(
                name="The Hoxton Shoreditch",
                location="London",
                amenities="WiFi, Restaurant, Bar, 24h Reception",
                rating=4.4,
            ),
            Hotel(
                name="Premier Inn London Bridge",
                location="London",
                amenities="WiFi, Restaurant, Breakfast, Parking",
                rating=4.1,
            ),
            Hotel(
                name="Hub by Premier Inn Kings Cross",
                location="London",
                amenities="WiFi, Bar, 24h Reception",
                rating=3.9,
            ),

            # ── Paris (4 hotels) ───────────────────────────────────────────────
            Hotel(
                name="Le Meurice Paris",
                location="Paris",
                amenities="WiFi, Michelin Restaurant, Spa, Concierge, Bar",
                rating=4.9,
            ),
            Hotel(
                name="Hotel des Arts Montmartre",
                location="Paris",
                amenities="WiFi, Breakfast, Bar, Garden Terrace",
                rating=4.5,
            ),
            Hotel(
                name="Ibis Paris Gare du Nord",
                location="Paris",
                amenities="WiFi, Restaurant, 24h Bar",
                rating=4.0,
            ),
            Hotel(
                name="Generator Paris",
                location="Paris",
                amenities="WiFi, Bar, Lounge, Rooftop",
                rating=3.8,
            ),

            # ── Dubai (4 hotels) ───────────────────────────────────────────────
            Hotel(
                name="Burj Al Arab Jumeirah",
                location="Dubai",
                amenities="WiFi, Private Beach, Pool, Spa, Helipad, Butler, Multiple Restaurants",
                rating=5.0,
            ),
            Hotel(
                name="Atlantis The Palm",
                location="Dubai",
                amenities="WiFi, Waterpark, Beach, Multiple Pools, Spa, Casino, Restaurants",
                rating=4.8,
            ),
            Hotel(
                name="JW Marriott Marquis Dubai",
                location="Dubai",
                amenities="WiFi, Pool, Spa, Gym, Multiple Restaurants, Business Centre",
                rating=4.6,
            ),
            Hotel(
                name="ibis Dubai Al Barsha",
                location="Dubai",
                amenities="WiFi, Restaurant, Pool, Parking",
                rating=3.9,
            ),

            # ── Barcelona (3 hotels) ───────────────────────────────────────────
            Hotel(
                name="Hotel Arts Barcelona",
                location="Barcelona",
                amenities="WiFi, Beach Access, Pool, Spa, Gym, Restaurants, Bar",
                rating=4.8,
            ),
            Hotel(
                name="Praktik Rambla",
                location="Barcelona",
                amenities="WiFi, Rooftop Pool, Bar, Concierge",
                rating=4.3,
            ),
            Hotel(
                name="Hostal Operaramblas",
                location="Barcelona",
                amenities="WiFi, 24h Reception, Breakfast",
                rating=3.7,
            ),

            # ── New York (2 hotels) ────────────────────────────────────────────
            Hotel(
                name="The Plaza New York",
                location="New York",
                amenities="WiFi, Spa, Fine Dining, Bar, Concierge, Fitness Centre",
                rating=4.7,
            ),
            Hotel(
                name="Pod 51 Hotel",
                location="New York",
                amenities="WiFi, Rooftop Bar, 24h Reception",
                rating=4.0,
            ),

            # ── Amsterdam (2 hotels) ───────────────────────────────────────────
            Hotel(
                name="Conservatorium Hotel Amsterdam",
                location="Amsterdam",
                amenities="WiFi, Spa, Pool, Restaurant, Bar, Brasserie",
                rating=4.8,
            ),
            Hotel(
                name="Stayokay Amsterdam Vondelpark",
                location="Amsterdam",
                amenities="WiFi, Restaurant, Bar, Bike Rental",
                rating=3.8,
            ),
        ]

        db.add_all(hotels)
        db.commit()
        for h in hotels:
            db.refresh(h)

        # ── Room Types ────────────────────────────────────────────────────────
        room_types = [
            # The Savoy London (h[0])
            RoomType(hotel_id=hotels[0].id, name="Classic Room",   capacity=2, price_per_night=450.0,  total_rooms=30),
            RoomType(hotel_id=hotels[0].id, name="Deluxe Room",    capacity=2, price_per_night=620.0,  total_rooms=20),
            RoomType(hotel_id=hotels[0].id, name="River Suite",    capacity=3, price_per_night=950.0,  total_rooms=8),
            RoomType(hotel_id=hotels[0].id, name="Royal Suite",    capacity=4, price_per_night=1800.0, total_rooms=2),

            # Claridge's (h[1])
            RoomType(hotel_id=hotels[1].id, name="Classic Room",   capacity=2, price_per_night=380.0,  total_rooms=25),
            RoomType(hotel_id=hotels[1].id, name="Deluxe Room",    capacity=2, price_per_night=520.0,  total_rooms=15),
            RoomType(hotel_id=hotels[1].id, name="Junior Suite",   capacity=3, price_per_night=780.0,  total_rooms=6),
            RoomType(hotel_id=hotels[1].id, name="Brook Penthouse",capacity=4, price_per_night=2200.0, total_rooms=1),

            # The Hoxton Shoreditch (h[2])
            RoomType(hotel_id=hotels[2].id, name="Shoebox",        capacity=1, price_per_night=89.0,   total_rooms=20),
            RoomType(hotel_id=hotels[2].id, name="Snug",           capacity=2, price_per_night=129.0,  total_rooms=30),
            RoomType(hotel_id=hotels[2].id, name="Roomy",          capacity=2, price_per_night=169.0,  total_rooms=15),
            RoomType(hotel_id=hotels[2].id, name="Biggy",          capacity=3, price_per_night=219.0,  total_rooms=8),

            # Premier Inn London Bridge (h[3])
            RoomType(hotel_id=hotels[3].id, name="Standard",       capacity=2, price_per_night=95.0,   total_rooms=50),
            RoomType(hotel_id=hotels[3].id, name="Superior",       capacity=3, price_per_night=125.0,  total_rooms=20),

            # Hub by Premier Inn Kings Cross (h[4])
            RoomType(hotel_id=hotels[4].id, name="Standard",       capacity=1, price_per_night=59.0,   total_rooms=80),
            RoomType(hotel_id=hotels[4].id, name="Standard Plus",  capacity=2, price_per_night=79.0,   total_rooms=40),

            # Le Meurice Paris (h[5])
            RoomType(hotel_id=hotels[5].id, name="Deluxe Room",    capacity=2, price_per_night=890.0,  total_rooms=20),
            RoomType(hotel_id=hotels[5].id, name="Prestige Suite", capacity=3, price_per_night=1400.0, total_rooms=8),
            RoomType(hotel_id=hotels[5].id, name="Belle Etoile",   capacity=4, price_per_night=3500.0, total_rooms=1),

            # Hotel des Arts Montmartre (h[6])
            RoomType(hotel_id=hotels[6].id, name="Classic",        capacity=2, price_per_night=135.0,  total_rooms=25),
            RoomType(hotel_id=hotels[6].id, name="Superior",       capacity=2, price_per_night=175.0,  total_rooms=12),
            RoomType(hotel_id=hotels[6].id, name="Junior Suite",   capacity=3, price_per_night=240.0,  total_rooms=4),

            # Ibis Paris Gare du Nord (h[7])
            RoomType(hotel_id=hotels[7].id, name="Standard",       capacity=2, price_per_night=78.0,   total_rooms=60),
            RoomType(hotel_id=hotels[7].id, name="Superior",       capacity=3, price_per_night=110.0,  total_rooms=20),

            # Generator Paris (h[8])
            RoomType(hotel_id=hotels[8].id, name="Private Room",   capacity=2, price_per_night=55.0,   total_rooms=40),
            RoomType(hotel_id=hotels[8].id, name="Ensuite Double", capacity=2, price_per_night=70.0,   total_rooms=20),

            # Burj Al Arab Jumeirah (h[9])
            RoomType(hotel_id=hotels[9].id, name="Deluxe Suite",   capacity=2, price_per_night=1500.0, total_rooms=20),
            RoomType(hotel_id=hotels[9].id, name="Sky Suite",      capacity=3, price_per_night=2500.0, total_rooms=12),
            RoomType(hotel_id=hotels[9].id, name="Royal Suite",    capacity=4, price_per_night=8000.0, total_rooms=2),

            # Atlantis The Palm (h[10])
            RoomType(hotel_id=hotels[10].id, name="Deluxe Room",   capacity=2, price_per_night=420.0,  total_rooms=40),
            RoomType(hotel_id=hotels[10].id, name="Palm Beach Suite", capacity=4, price_per_night=950.0, total_rooms=10),
            RoomType(hotel_id=hotels[10].id, name="Underwater Suite", capacity=2, price_per_night=3200.0, total_rooms=3),

            # JW Marriott Marquis Dubai (h[11])
            RoomType(hotel_id=hotels[11].id, name="Deluxe King",   capacity=2, price_per_night=280.0,  total_rooms=50),
            RoomType(hotel_id=hotels[11].id, name="Executive",     capacity=2, price_per_night=380.0,  total_rooms=25),
            RoomType(hotel_id=hotels[11].id, name="Suite",         capacity=4, price_per_night=580.0,  total_rooms=10),

            # ibis Dubai Al Barsha (h[12])
            RoomType(hotel_id=hotels[12].id, name="Standard",      capacity=2, price_per_night=65.0,   total_rooms=70),
            RoomType(hotel_id=hotels[12].id, name="Superior",      capacity=3, price_per_night=90.0,   total_rooms=20),

            # Hotel Arts Barcelona (h[13])
            RoomType(hotel_id=hotels[13].id, name="Deluxe Room",   capacity=2, price_per_night=320.0,  total_rooms=30),
            RoomType(hotel_id=hotels[13].id, name="Sea View Room", capacity=2, price_per_night=420.0,  total_rooms=15),
            RoomType(hotel_id=hotels[13].id, name="Junior Suite",  capacity=3, price_per_night=620.0,  total_rooms=8),
            RoomType(hotel_id=hotels[13].id, name="Arts Suite",    capacity=4, price_per_night=1100.0, total_rooms=3),

            # Praktik Rambla (h[14])
            RoomType(hotel_id=hotels[14].id, name="Standard",      capacity=2, price_per_night=110.0,  total_rooms=20),
            RoomType(hotel_id=hotels[14].id, name="Superior",      capacity=2, price_per_night=145.0,  total_rooms=10),
            RoomType(hotel_id=hotels[14].id, name="Terrace Room",  capacity=3, price_per_night=195.0,  total_rooms=5),

            # Hostal Operaramblas (h[15])
            RoomType(hotel_id=hotels[15].id, name="Standard",      capacity=2, price_per_night=55.0,   total_rooms=30),
            RoomType(hotel_id=hotels[15].id, name="Triple",        capacity=3, price_per_night=75.0,   total_rooms=10),

            # The Plaza New York (h[16])
            RoomType(hotel_id=hotels[16].id, name="Classic Room",  capacity=2, price_per_night=650.0,  total_rooms=25),
            RoomType(hotel_id=hotels[16].id, name="Edwardian Suite", capacity=3, price_per_night=1200.0, total_rooms=10),
            RoomType(hotel_id=hotels[16].id, name="Central Park Suite", capacity=4, price_per_night=2500.0, total_rooms=3),

            # Pod 51 Hotel (h[17])
            RoomType(hotel_id=hotels[17].id, name="Pod Single",    capacity=1, price_per_night=99.0,   total_rooms=60),
            RoomType(hotel_id=hotels[17].id, name="Pod Double",    capacity=2, price_per_night=139.0,  total_rooms=40),
            RoomType(hotel_id=hotels[17].id, name="Quad",          capacity=4, price_per_night=189.0,  total_rooms=10),

            # Conservatorium Hotel Amsterdam (h[18])
            RoomType(hotel_id=hotels[18].id, name="Superior Room", capacity=2, price_per_night=320.0,  total_rooms=20),
            RoomType(hotel_id=hotels[18].id, name="Deluxe Room",   capacity=2, price_per_night=420.0,  total_rooms=15),
            RoomType(hotel_id=hotels[18].id, name="Junior Suite",  capacity=3, price_per_night=650.0,  total_rooms=6),

            # Stayokay Amsterdam Vondelpark (h[19])
            RoomType(hotel_id=hotels[19].id, name="Private Double", capacity=2, price_per_night=72.0,  total_rooms=25),
            RoomType(hotel_id=hotels[19].id, name="Private Triple", capacity=3, price_per_night=95.0,  total_rooms=10),
        ]

        db.add_all(room_types)
        db.commit()
        for rt in room_types:
            db.refresh(rt)

        # ── Bookings (realistic existing reservations) ─────────────────────────
        # These create real availability constraints for upcoming dates.
        # rt indices map directly to the room_types list above.
        bookings = [
            # London — The Savoy, Classic Rooms heavily booked over Easter
            Booking(booking_reference="BK-LON001", hotel_id=hotels[0].id, room_type_id=room_types[0].id,
                    user_name="James Whitfield",    user_email="j.whitfield@email.com",
                    check_in=date(2026, 4, 2),  check_out=date(2026, 4, 6),  guests=2,
                    booked_price_per_night=450.0, total_price=1800.0, currency="GBP", status="confirmed"),
            Booking(booking_reference="BK-LON002", hotel_id=hotels[0].id, room_type_id=room_types[0].id,
                    user_name="Sophie Turner",      user_email="s.turner@email.com",
                    check_in=date(2026, 4, 3),  check_out=date(2026, 4, 7),  guests=2,
                    booked_price_per_night=450.0, total_price=1800.0, currency="GBP", status="confirmed"),
            Booking(booking_reference="BK-LON003", hotel_id=hotels[0].id, room_type_id=room_types[2].id,
                    user_name="Richard Branson Jr", user_email="rbj@corp.com",
                    check_in=date(2026, 4, 10), check_out=date(2026, 4, 14), guests=3,
                    booked_price_per_night=950.0, total_price=3800.0, currency="GBP", status="confirmed"),

            # London — Claridge's
            Booking(booking_reference="BK-LON004", hotel_id=hotels[1].id, room_type_id=room_types[4].id,
                    user_name="Emma Clarke",        user_email="emma.c@email.com",
                    check_in=date(2026, 4, 15), check_out=date(2026, 4, 19), guests=2,
                    booked_price_per_night=380.0, total_price=1520.0, currency="GBP", status="confirmed"),

            # London — Hoxton Shoreditch (popular, lots of bookings)
            Booking(booking_reference="BK-LON005", hotel_id=hotels[2].id, room_type_id=room_types[9].id,
                    user_name="Liam Gallagher",     user_email="liam.g@email.com",
                    check_in=date(2026, 4, 5),  check_out=date(2026, 4, 8),  guests=2,
                    booked_price_per_night=129.0, total_price=387.0,  currency="GBP", status="confirmed"),
            Booking(booking_reference="BK-LON006", hotel_id=hotels[2].id, room_type_id=room_types[9].id,
                    user_name="Priya Patel",        user_email="priya.p@email.com",
                    check_in=date(2026, 4, 6),  check_out=date(2026, 4, 9),  guests=2,
                    booked_price_per_night=129.0, total_price=387.0,  currency="GBP", status="confirmed"),

            # London — Premier Inn (budget option, very busy)
            Booking(booking_reference="BK-LON007", hotel_id=hotels[3].id, room_type_id=room_types[12].id,
                    user_name="David Mitchell",     user_email="d.mitchell@email.com",
                    check_in=date(2026, 4, 1),  check_out=date(2026, 4, 5),  guests=2,
                    booked_price_per_night=95.0,  total_price=380.0,  currency="GBP", status="confirmed"),
            Booking(booking_reference="BK-LON008", hotel_id=hotels[3].id, room_type_id=room_types[12].id,
                    user_name="Charlotte Webb",     user_email="c.webb@email.com",
                    check_in=date(2026, 4, 2),  check_out=date(2026, 4, 6),  guests=1,
                    booked_price_per_night=95.0,  total_price=380.0,  currency="GBP", status="confirmed"),

            # Paris — Le Meurice
            Booking(booking_reference="BK-PAR001", hotel_id=hotels[5].id, room_type_id=room_types[16].id,
                    user_name="Jean-Pierre Moreau", user_email="jp.moreau@email.fr",
                    check_in=date(2026, 4, 8),  check_out=date(2026, 4, 12), guests=2,
                    booked_price_per_night=890.0, total_price=3560.0, currency="EUR", status="confirmed"),
            Booking(booking_reference="BK-PAR002", hotel_id=hotels[5].id, room_type_id=room_types[17].id,
                    user_name="Isabelle Laurent",   user_email="i.laurent@corp.fr",
                    check_in=date(2026, 4, 20), check_out=date(2026, 4, 24), guests=3,
                    booked_price_per_night=1400.0, total_price=5600.0, currency="EUR", status="confirmed"),

            # Paris — Hotel des Arts
            Booking(booking_reference="BK-PAR003", hotel_id=hotels[6].id, room_type_id=room_types[19].id,
                    user_name="Anna Kowalski",      user_email="a.kowalski@email.pl",
                    check_in=date(2026, 5, 1),  check_out=date(2026, 5, 5),  guests=2,
                    booked_price_per_night=135.0, total_price=540.0,  currency="EUR", status="confirmed"),

            # Paris — Ibis (budget)
            Booking(booking_reference="BK-PAR004", hotel_id=hotels[7].id, room_type_id=room_types[22].id,
                    user_name="Marco Russo",        user_email="m.russo@email.it",
                    check_in=date(2026, 4, 12), check_out=date(2026, 4, 15), guests=2,
                    booked_price_per_night=78.0,  total_price=234.0,  currency="EUR", status="confirmed"),

            # Dubai — Burj Al Arab (ultra-luxury, limited rooms)
            Booking(booking_reference="BK-DXB001", hotel_id=hotels[9].id, room_type_id=room_types[26].id,
                    user_name="Sheikh Mohammed Al-Rashid", user_email="m.alrashid@vip.ae",
                    check_in=date(2026, 4, 5),  check_out=date(2026, 4, 12), guests=2,
                    booked_price_per_night=1500.0, total_price=10500.0, currency="AED", status="confirmed"),
            Booking(booking_reference="BK-DXB002", hotel_id=hotels[9].id, room_type_id=room_types[28].id,
                    user_name="Elon Musk",          user_email="e.musk@corp.com",
                    check_in=date(2026, 4, 1),  check_out=date(2026, 4, 3),  guests=4,
                    booked_price_per_night=8000.0, total_price=16000.0, currency="AED", status="confirmed"),

            # Dubai — Atlantis
            Booking(booking_reference="BK-DXB003", hotel_id=hotels[10].id, room_type_id=room_types[29].id,
                    user_name="Chen Wei",           user_email="c.wei@email.cn",
                    check_in=date(2026, 4, 18), check_out=date(2026, 4, 23), guests=2,
                    booked_price_per_night=420.0, total_price=2100.0, currency="AED", status="confirmed"),
            Booking(booking_reference="BK-DXB004", hotel_id=hotels[10].id, room_type_id=room_types[30].id,
                    user_name="Carlos Fernandez",   user_email="c.fernandez@email.es",
                    check_in=date(2026, 5, 10), check_out=date(2026, 5, 17), guests=4,
                    booked_price_per_night=950.0, total_price=6650.0, currency="AED", status="confirmed"),

            # Dubai — JW Marriott
            Booking(booking_reference="BK-DXB005", hotel_id=hotels[11].id, room_type_id=room_types[32].id,
                    user_name="Fatima Al-Hassan",   user_email="f.alhassan@email.ae",
                    check_in=date(2026, 4, 7),  check_out=date(2026, 4, 10), guests=2,
                    booked_price_per_night=280.0, total_price=840.0,  currency="AED", status="confirmed"),

            # Barcelona — Hotel Arts
            Booking(booking_reference="BK-BCN001", hotel_id=hotels[13].id, room_type_id=room_types[37].id,
                    user_name="Pablo Sanchez",      user_email="p.sanchez@email.es",
                    check_in=date(2026, 4, 25), check_out=date(2026, 4, 30), guests=2,
                    booked_price_per_night=420.0, total_price=2100.0, currency="EUR", status="confirmed"),
            Booking(booking_reference="BK-BCN002", hotel_id=hotels[13].id, room_type_id=room_types[38].id,
                    user_name="Giulia Romano",      user_email="g.romano@email.it",
                    check_in=date(2026, 5, 3),  check_out=date(2026, 5, 7),  guests=3,
                    booked_price_per_night=620.0, total_price=2480.0, currency="EUR", status="confirmed"),

            # Barcelona — Praktik
            Booking(booking_reference="BK-BCN003", hotel_id=hotels[14].id, room_type_id=room_types[41].id,
                    user_name="Lars Johansson",     user_email="l.johansson@email.se",
                    check_in=date(2026, 4, 14), check_out=date(2026, 4, 18), guests=2,
                    booked_price_per_night=110.0, total_price=440.0,  currency="EUR", status="confirmed"),

            # New York — The Plaza
            Booking(booking_reference="BK-NYC001", hotel_id=hotels[16].id, room_type_id=room_types[47].id,
                    user_name="Jennifer Adams",     user_email="j.adams@email.com",
                    check_in=date(2026, 4, 10), check_out=date(2026, 4, 14), guests=2,
                    booked_price_per_night=650.0, total_price=2600.0, currency="USD", status="confirmed"),
            Booking(booking_reference="BK-NYC002", hotel_id=hotels[16].id, room_type_id=room_types[48].id,
                    user_name="Michael Bloomberg Jr", user_email="m.bloomberg@corp.com",
                    check_in=date(2026, 4, 22), check_out=date(2026, 4, 26), guests=3,
                    booked_price_per_night=1200.0, total_price=4800.0, currency="USD", status="confirmed"),

            # New York — Pod 51
            Booking(booking_reference="BK-NYC003", hotel_id=hotels[17].id, room_type_id=room_types[51].id,
                    user_name="Yuki Tanaka",        user_email="y.tanaka@email.jp",
                    check_in=date(2026, 4, 8),  check_out=date(2026, 4, 11), guests=2,
                    booked_price_per_night=139.0, total_price=417.0,  currency="USD", status="confirmed"),

            # Amsterdam — Conservatorium
            Booking(booking_reference="BK-AMS001", hotel_id=hotels[18].id, room_type_id=room_types[53].id,
                    user_name="Hans van der Berg",  user_email="h.vanderberg@email.nl",
                    check_in=date(2026, 4, 17), check_out=date(2026, 4, 21), guests=2,
                    booked_price_per_night=320.0, total_price=1280.0, currency="EUR", status="confirmed"),

            # Amsterdam — Stayokay
            Booking(booking_reference="BK-AMS002", hotel_id=hotels[19].id, room_type_id=room_types[56].id,
                    user_name="Maria Santos",       user_email="m.santos@email.pt",
                    check_in=date(2026, 4, 5),  check_out=date(2026, 4, 9),  guests=2,
                    booked_price_per_night=72.0,  total_price=288.0,  currency="EUR", status="confirmed"),
        ]

        db.add_all(bookings)
        db.commit()

        print(f"\n✅ Seeded {len(hotels)} hotels")
        print(f"✅ Seeded {len(room_types)} room types")
        print(f"✅ Seeded {len(bookings)} bookings")
        print("\n📍 Cities covered:")
        cities = {}
        for h in hotels:
            cities[h.location] = cities.get(h.location, 0) + 1
        for city, count in sorted(cities.items()):
            print(f"   {city}: {count} hotel(s)")
        print("\n💷 Price range per city:")
        for h in hotels:
            prices = [rt.price_per_night for rt in room_types if rt.hotel_id == h.id]
            if prices:
                print(f"   {h.name:<40} £{min(prices):.0f} – £{max(prices):.0f}/night")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Wipe and re-seed")
    args = parser.parse_args()
    seed(force=args.force)
