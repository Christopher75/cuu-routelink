"""
Management command to seed sample bus data for CUU RouteLink.
Creates routes across three categories:
  1. Campus Routes     – between CUU campuses
  2. Campus-City Routes – campus ↔ Kampala CBD / Entebbe / Jinja
  3. Intercity Routes  – major Uganda cities (student holiday travel)

Schedules are generated from today up to June 2026.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from Bus.models import Place, BusOperator, Bus, Banner

User = get_user_model()


def dt(days_offset, hour, minute=0):
    """Return a timezone-aware datetime: midnight today + offset."""
    base = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(days=days_offset, hours=hour, minutes=minute)


class Command(BaseCommand):
    help = 'Seeds CUU RouteLink with buses, routes, and schedules up to June 2026'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding CUU RouteLink data...')

        # ── Superuser ─────────────────────────────────────────────
        if not User.objects.filter(email='admin@cuuroute.ug').exists():
            User.objects.create_superuser(
                username='admin@cuuroute.ug',
                email='admin@cuuroute.ug',
                password='Admin@1234',
                first_name='System Admin',
            )
            self.stdout.write(self.style.SUCCESS('  Created superuser: admin@cuuroute.ug / Admin@1234'))

        # ── Fetch Places ──────────────────────────────────────────
        def place(name):
            try:
                return Place.objects.get(place_name=name)
            except Place.DoesNotExist:
                self.stderr.write(f'  Place not found: {name} — run migrate first.')
                return None

        nsambya  = place('CUU Main Campus Nsambya')
        acacia   = place('CUU Law Campus Acacia')
        mukono   = place('CUU Mukono Campus')
        kampala  = place('Kampala')
        entebbe  = place('Entebbe')
        jinja    = place('Jinja')
        mbarara  = place('Mbarara')
        gulu     = place('Gulu')
        mbale    = place('Mbale')
        kabale   = place('Kabale')
        fortprt  = place('Fort Portal')
        lira     = place('Lira')
        arua     = place('Arua')
        soroti   = place('Soroti')
        hoima    = place('Hoima')
        masaka   = place('Masaka')
        tororo   = place('Tororo')
        kasese   = place('Kasese')

        if None in [nsambya, acacia, mukono, kampala]:
            self.stderr.write('Critical places missing. Aborting seed.')
            return

        # ── Operators (get or create to be safe) ─────────────────
        def op(name, contact='+256700000000'):
            obj, _ = BusOperator.objects.get_or_create(
                operator_name=name, defaults={'operator_contact': contact})
            return obj

        shuttle   = op('CUU Campus Shuttle',   '+256700777888')
        ugexpress = op('Uganda Bus Express',   '+256700111222')
        linkbus   = op('Link Bus Services',    '+256700333444')
        postbus   = op('Post Bus Uganda',      '+256700555666')
        eagle     = op('Eagle Express Uganda', '+256701234567')
        horizon   = op('Horizon Bus Lines',    '+256702345678')

        # ── Helper: create bus if it doesn't exist ────────────────
        created = 0

        def add(name, src, dst, bus_type, fare, dep_day, dep_hr, dep_min,
                arr_day, arr_hr, arr_min, seats, operator, policy, amenities):
            nonlocal created
            obj, new = Bus.objects.get_or_create(
                bus_name=name,
                source=src,
                destination=dst,
                defaults=dict(
                    bus_type=bus_type,
                    fare=fare,
                    starting_time=dt(dep_day, dep_hr, dep_min),
                    arrival_time=dt(arr_day, arr_hr, arr_min),
                    seats=seats,
                    bus_operator=operator,
                    cancel_policy=policy,
                    amenities=amenities,
                    is_available=True,
                    status='Scheduled',
                )
            )
            if new:
                created += 1

        FREE24  = 'Free cancellation 24 hours before departure'
        FREE48  = 'Free cancellation 48 hours before departure'
        FREE12  = 'Free cancellation 12 hours before departure'
        NORFND  = 'Non-refundable after booking'
        HALF6   = '50% refund if cancelled 6 hours before departure'

        # ══════════════════════════════════════════════════════════
        # CATEGORY 1 — CAMPUS ROUTES
        # Nsambya ↔ Acacia ↔ Mukono (daily, affordable, frequent)
        # ══════════════════════════════════════════════════════════

        # ── Nsambya → Acacia ──────────────────────────────────────
        campus_nsa_aca = [
            # (label_suffix, dep_day, dep_hr, dep_min)
            ('Morning Run',   1,  7, 0),   ('Midday Run',     1, 12,30),
            ('Afternoon Run', 1, 17, 0),   ('Morning Run',    3,  7, 0),
            ('Midday Run',    3, 12,30),   ('Afternoon Run',  3, 17, 0),
            ('Morning Run',   5,  7, 0),   ('Midday Run',     5, 12,30),
            ('Morning Run',   8,  7, 0),   ('Afternoon Run',  8, 17, 0),
            ('Morning Run',  12,  7, 0),   ('Midday Run',    12, 12,30),
            ('Afternoon Run',12, 17, 0),   ('Morning Run',   15,  7, 0),
            ('Afternoon Run',15, 17, 0),   ('Morning Run',   19,  7, 0),
            ('Midday Run',   19, 12,30),   ('Morning Run',   22,  7, 0),
            ('Afternoon Run',22, 17, 0),   ('Morning Run',   26,  7, 0),
            ('Morning Run',  29,  7, 0),   ('Afternoon Run', 29, 17, 0),
            ('Morning Run',  33,  7, 0),   ('Midday Run',    33, 12,30),
            ('Morning Run',  36,  7, 0),   ('Afternoon Run', 36, 17, 0),
            ('Morning Run',  40,  7, 0),   ('Midday Run',    40, 12,30),
            ('Morning Run',  43,  7, 0),   ('Afternoon Run', 43, 17, 0),
            ('Morning Run',  47,  7, 0),   ('Morning Run',   50,  7, 0),
            ('Afternoon Run',50, 17, 0),   ('Morning Run',   54,  7, 0),
            ('Morning Run',  57,  7, 0),   ('Afternoon Run', 57, 17, 0),
            ('Morning Run',  61,  7, 0),   ('Morning Run',   64,  7, 0),
            ('Afternoon Run',64, 17, 0),   ('Morning Run',   68,  7, 0),
            ('Morning Run',  71,  7, 0),   ('Afternoon Run', 71, 17, 0),
            ('Morning Run',  75,  7, 0),   ('Morning Run',   78,  7, 0),
            ('Afternoon Run',78, 17, 0),   ('Morning Run',   82,  7, 0),
            ('Morning Run',  85,  7, 0),   ('Afternoon Run', 85, 17, 0),
            ('Morning Run',  89,  7, 0),   ('Morning Run',   92,  7, 0),
            ('Afternoon Run',92, 17, 0),   ('Morning Run',   96,  7, 0),
            ('Morning Run',  99,  7, 0),   ('Afternoon Run', 99, 17, 0),
        ]
        for suffix, dd, dh, dm in campus_nsa_aca:
            add(f'CUU Shuttle NSA→ACA {suffix} D{dd}',
                nsambya, acacia, 'Campus Shuttle', 2000,
                dd, dh, dm, dd, dh+0, dm+30, 20,
                shuttle, FREE12, 'Campus WiFi,USB Charging')

        # ── Acacia → Nsambya ──────────────────────────────────────
        campus_aca_nsa = [
            ('Morning',   1,  8,30),('Evening',    1, 18, 0),
            ('Morning',   3,  8,30),('Evening',    3, 18, 0),
            ('Morning',   5,  8,30),('Evening',    5, 18, 0),
            ('Morning',   8,  8,30),('Evening',    8, 18, 0),
            ('Morning',  12,  8,30),('Evening',   12, 18, 0),
            ('Morning',  15,  8,30),('Evening',   15, 18, 0),
            ('Morning',  19,  8,30),('Evening',   19, 18, 0),
            ('Morning',  22,  8,30),('Evening',   22, 18, 0),
            ('Morning',  26,  8,30),('Evening',   26, 18, 0),
            ('Morning',  29,  8,30),('Evening',   29, 18, 0),
            ('Morning',  33,  8,30),('Evening',   33, 18, 0),
            ('Morning',  36,  8,30),('Evening',   36, 18, 0),
            ('Morning',  40,  8,30),('Evening',   40, 18, 0),
            ('Morning',  43,  8,30),('Evening',   43, 18, 0),
            ('Morning',  47,  8,30),('Evening',   47, 18, 0),
            ('Morning',  50,  8,30),('Evening',   50, 18, 0),
            ('Morning',  54,  8,30),('Evening',   54, 18, 0),
            ('Morning',  57,  8,30),('Evening',   57, 18, 0),
            ('Morning',  61,  8,30),('Evening',   61, 18, 0),
            ('Morning',  64,  8,30),('Evening',   64, 18, 0),
            ('Morning',  68,  8,30),('Evening',   68, 18, 0),
            ('Morning',  71,  8,30),('Evening',   71, 18, 0),
            ('Morning',  75,  8,30),('Evening',   75, 18, 0),
            ('Morning',  78,  8,30),('Evening',   78, 18, 0),
            ('Morning',  82,  8,30),('Evening',   82, 18, 0),
            ('Morning',  85,  8,30),('Evening',   85, 18, 0),
            ('Morning',  89,  8,30),('Evening',   89, 18, 0),
            ('Morning',  92,  8,30),('Evening',   92, 18, 0),
            ('Morning',  96,  8,30),('Evening',   96, 18, 0),
            ('Morning',  99,  8,30),('Evening',   99, 18, 0),
        ]
        for suffix, dd, dh, dm in campus_aca_nsa:
            add(f'CUU Shuttle ACA→NSA {suffix} D{dd}',
                acacia, nsambya, 'Campus Shuttle', 2000,
                dd, dh, dm, dd, dh, dm+30, 20,
                shuttle, FREE12, 'Campus WiFi,USB Charging')

        # ── Nsambya → Mukono ─────────────────────────────────────
        nsa_muk_trips = [
            (2,  7, 0),(4, 7, 0),(7, 7, 0),(9, 7, 0),(11,7,0),
            (14, 7, 0),(16,7, 0),(18,7, 0),(21,7, 0),(23,7,0),
            (25, 7, 0),(28,7, 0),(30,7, 0),(32,7, 0),(35,7,0),
            (37, 7, 0),(39,7, 0),(42,7, 0),(44,7, 0),(46,7,0),
            (49, 7, 0),(51,7, 0),(53,7, 0),(56,7, 0),(58,7,0),
            (60, 7, 0),(63,7, 0),(65,7, 0),(67,7, 0),(70,7,0),
            (72, 7, 0),(74,7, 0),(77,7, 0),(79,7, 0),(81,7,0),
            (84, 7, 0),(86,7, 0),(88,7, 0),(91,7, 0),(93,7,0),
            (95, 7, 0),(98,7, 0),(100,7,0),
        ]
        for dd, dh, dm in nsa_muk_trips:
            add(f'CUU Express NSA→MUK D{dd}',
                nsambya, mukono, 'Campus Shuttle', 3500,
                dd, dh, dm, dd, dh+1, dm+15, 25,
                shuttle, FREE12, 'Campus WiFi,USB Charging,AC')

        # ── Mukono → Nsambya ─────────────────────────────────────
        muk_nsa_trips = [
            (2, 17,30),(4,17,30),(7,17,30),(9,17,30),(11,17,30),
            (14,17,30),(16,17,30),(18,17,30),(21,17,30),(23,17,30),
            (25,17,30),(28,17,30),(30,17,30),(32,17,30),(35,17,30),
            (37,17,30),(39,17,30),(42,17,30),(44,17,30),(46,17,30),
            (49,17,30),(51,17,30),(53,17,30),(56,17,30),(58,17,30),
            (60,17,30),(63,17,30),(65,17,30),(67,17,30),(70,17,30),
            (72,17,30),(74,17,30),(77,17,30),(79,17,30),(81,17,30),
            (84,17,30),(86,17,30),(88,17,30),(91,17,30),(93,17,30),
            (95,17,30),(98,17,30),(100,17,30),
        ]
        for dd, dh, dm in muk_nsa_trips:
            add(f'CUU Express MUK→NSA D{dd}',
                mukono, nsambya, 'Campus Shuttle', 3500,
                dd, dh, dm, dd, dh+1, dm+15, 25,
                shuttle, FREE12, 'Campus WiFi,USB Charging,AC')

        # ── Acacia → Mukono ──────────────────────────────────────
        aca_muk = [(2,8,0),(6,8,0),(9,8,0),(13,8,0),(16,8,0),(20,8,0),
                   (23,8,0),(27,8,0),(30,8,0),(34,8,0),(37,8,0),(41,8,0),
                   (44,8,0),(48,8,0),(51,8,0),(55,8,0),(58,8,0),(62,8,0),
                   (65,8,0),(69,8,0),(72,8,0),(76,8,0),(79,8,0),(83,8,0),
                   (86,8,0),(90,8,0),(93,8,0),(97,8,0),(100,8,0)]
        for dd, dh, dm in aca_muk:
            add(f'CUU Link ACA→MUK D{dd}',
                acacia, mukono, 'Campus Shuttle', 4000,
                dd, dh, dm, dd, dh+1, dm+30, 22,
                shuttle, FREE12, 'Campus WiFi,USB Charging,AC')

        # ── Mukono → Acacia ──────────────────────────────────────
        for dd, dh, dm in aca_muk:
            add(f'CUU Link MUK→ACA D{dd}',
                mukono, acacia, 'Campus Shuttle', 4000,
                dd, dh+10, dm, dd, dh+11, dm+30, 22,
                shuttle, FREE12, 'Campus WiFi,USB Charging,AC')

        # ══════════════════════════════════════════════════════════
        # CATEGORY 2 — CAMPUS-CITY ROUTES
        # Campus ↔ Kampala CBD / Entebbe / Jinja
        # ══════════════════════════════════════════════════════════

        # ── Nsambya → Kampala CBD ─────────────────────────────────
        nsa_kla = [(1,6,30),(2,6,30),(3,6,30),(4,6,30),(5,6,30),(6,6,30),
                   (8,6,30),(9,6,30),(10,6,30),(11,6,30),(12,6,30),
                   (15,6,30),(16,6,30),(17,6,30),(18,6,30),(19,6,30),
                   (22,6,30),(23,6,30),(24,6,30),(25,6,30),(26,6,30),
                   (29,6,30),(30,6,30),(31,6,30),(32,6,30),(33,6,30),
                   (36,6,30),(37,6,30),(38,6,30),(39,6,30),(40,6,30),
                   (43,6,30),(44,6,30),(45,6,30),(46,6,30),(47,6,30),
                   (50,6,30),(51,6,30),(52,6,30),(53,6,30),(54,6,30),
                   (57,6,30),(58,6,30),(59,6,30),(60,6,30),(61,6,30),
                   (64,6,30),(65,6,30),(66,6,30),(67,6,30),(68,6,30),
                   (71,6,30),(72,6,30),(73,6,30),(74,6,30),(75,6,30),
                   (78,6,30),(79,6,30),(80,6,30),(81,6,30),(82,6,30),
                   (85,6,30),(86,6,30),(87,6,30),(88,6,30),(89,6,30),
                   (92,6,30),(93,6,30),(94,6,30),(95,6,30),(96,6,30),
                   (99,6,30),(100,6,30)]
        for dd, dh, dm in nsa_kla:
            add(f'CUU City Rider NSA→KLA D{dd}',
                nsambya, kampala, 'Campus-City', 3000,
                dd, dh, dm, dd, dh+0, dm+45, 30,
                shuttle, FREE12, 'Campus WiFi,USB Charging')

        # ── Kampala CBD → Nsambya ────────────────────────────────
        kla_nsa_times = [(dd, 16, 30) for (dd, _, __) in nsa_kla]
        for dd, dh, dm in kla_nsa_times:
            add(f'CUU City Rider KLA→NSA D{dd}',
                kampala, nsambya, 'Campus-City', 3000,
                dd, dh, dm, dd, dh+0, dm+45, 30,
                shuttle, FREE12, 'Campus WiFi,USB Charging')

        # ── Acacia → Kampala CBD ──────────────────────────────────
        aca_kla_days = [1,2,3,4,5,8,9,10,11,12,15,16,17,18,19,
                        22,23,24,25,26,29,30,31,32,33,36,37,38,39,40,
                        43,44,45,46,47,50,51,52,53,54,57,58,59,60,61,
                        64,65,66,67,68,71,72,73,74,75,78,79,80,81,82,
                        85,86,87,88,89,92,93,94,95,96,99,100]
        for dd in aca_kla_days:
            add(f'CUU City Rider ACA→KLA D{dd}',
                acacia, kampala, 'Campus-City', 2500,
                dd, 6, 45, dd, 7, 30, 28,
                shuttle, FREE12, 'Campus WiFi,USB Charging')
            add(f'CUU City Rider KLA→ACA D{dd}',
                kampala, acacia, 'Campus-City', 2500,
                dd, 17, 0, dd, 17, 45, 28,
                shuttle, FREE12, 'Campus WiFi,USB Charging')

        # ── Mukono → Kampala CBD ──────────────────────────────────
        muk_kla_days = [1,3,5,7,9,11,14,16,18,20,22,25,27,29,32,34,
                        36,39,41,43,46,48,50,53,55,57,60,62,64,67,69,
                        71,74,76,78,81,83,85,88,90,92,95,97,99]
        for dd in muk_kla_days:
            add(f'CUU City Express MUK→KLA D{dd}',
                mukono, kampala, 'Campus-City', 5000,
                dd, 6, 0, dd, 7, 15, 35,
                ugexpress, FREE12, 'AC,USB Charging,Campus WiFi')
            add(f'CUU City Express KLA→MUK D{dd}',
                kampala, mukono, 'Campus-City', 5000,
                dd, 17, 30, dd, 18, 45, 35,
                ugexpress, FREE12, 'AC,USB Charging,Campus WiFi')

        # ── Campus → Entebbe (airport trips / weekend) ───────────
        entebbe_trips = [
            (5,  nsambya, entebbe, 4000, 6, 0, 7, 15),
            (12, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (19, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (26, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (33, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (40, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (47, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (54, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (61, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (68, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (75, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (82, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (89, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (96, nsambya, entebbe, 4000, 6, 0, 7, 15),
            (5,  acacia,  entebbe, 3500, 6,30, 7,45),
            (12, acacia,  entebbe, 3500, 6,30, 7,45),
            (19, acacia,  entebbe, 3500, 6,30, 7,45),
            (26, acacia,  entebbe, 3500, 6,30, 7,45),
            (33, acacia,  entebbe, 3500, 6,30, 7,45),
            (40, acacia,  entebbe, 3500, 6,30, 7,45),
            (47, acacia,  entebbe, 3500, 6,30, 7,45),
            (54, acacia,  entebbe, 3500, 6,30, 7,45),
            (61, acacia,  entebbe, 3500, 6,30, 7,45),
            (68, acacia,  entebbe, 3500, 6,30, 7,45),
            (75, acacia,  entebbe, 3500, 6,30, 7,45),
            (82, acacia,  entebbe, 3500, 6,30, 7,45),
            (89, acacia,  entebbe, 3500, 6,30, 7,45),
            (96, acacia,  entebbe, 3500, 6,30, 7,45),
        ]
        for dd, src, dst, fare, dh, dm, ah, am in entebbe_trips:
            lbl = 'NSA' if src == nsambya else 'ACA'
            add(f'CUU Airport Shuttle {lbl}→ENT D{dd}',
                src, dst, 'Campus-City', fare,
                dd, dh, dm, dd, ah, am, 20,
                shuttle, FREE12, 'AC,USB Charging')

        # ── Campus → Jinja (day trip Fridays) ────────────────────
        jinja_fridays = [3,10,17,24,31,38,45,52,59,66,73,80,87,94]
        for dd in jinja_fridays:
            add(f'CUU Jinja Day Trip NSA D{dd}',
                nsambya, jinja, 'Campus-City', 8000,
                dd, 7, 0, dd, 9, 0, 28,
                linkbus, HALF6, 'AC,USB Charging,Snacks')
            add(f'CUU Jinja Return JNJ→NSA D{dd}',
                jinja, nsambya, 'Campus-City', 8000,
                dd, 17, 0, dd, 19, 0, 28,
                linkbus, HALF6, 'AC,USB Charging,Snacks')

        # ══════════════════════════════════════════════════════════
        # CATEGORY 3 — INTERCITY ROUTES (Student Holiday Travel)
        # Spreads across March-June 2026 (days 0–101 from today)
        # ══════════════════════════════════════════════════════════

        intercity = []

        # ── Kampala → Mbarara ─────────────────────────────────────
        for dd in [2,5,7,9,12,14,16,19,21,23,26,28,30,33,35,37,40,42,
                   44,47,49,51,54,56,58,61,63,65,68,70,72,75,77,79,82,
                   84,86,89,91,93,96,98,100]:
            intercity.append(dict(
                bus_name=f'Pearl Express KLA→MBA D{dd}',
                src=kampala, dst=mbarara, bus_type='AC', fare=25000,
                dd=dd, dh=7, dm=0, ah=12, am=0, seats=45,
                op=ugexpress, policy=FREE24,
                am_str='AC,WiFi,USB Charging,Recliner Seats'))
            intercity.append(dict(
                bus_name=f'Victoria Coach KLA→MBA D{dd}',
                src=kampala, dst=mbarara, bus_type='Non-AC', fare=18000,
                dd=dd, dh=14, dm=0, ah=19, am=0, seats=55,
                op=linkbus, policy=NORFND, am_str='USB Charging'))

        # ── Mbarara → Kampala ─────────────────────────────────────
        for dd in [2,5,7,9,12,14,16,19,21,23,26,28,30,33,35,37,40,42,
                   44,47,49,51,54,56,58,61,63,65,68,70,72,75,77,79,82,
                   84,86,89,91,93,96,98,100]:
            intercity.append(dict(
                bus_name=f'Victoria Link MBA→KLA D{dd}',
                src=mbarara, dst=kampala, bus_type='AC', fare=25000,
                dd=dd, dh=5, dm=0, ah=10, am=0, seats=45,
                op=ugexpress, policy=FREE24, am_str='AC,WiFi,USB Charging'))

        # ── Kampala → Gulu ───────────────────────────────────────
        for dd in [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,46,49,
                   52,55,58,61,64,67,70,73,76,79,82,85,88,91,94,97,100]:
            intercity.append(dict(
                bus_name=f'Nile Star KLA→GUL D{dd}',
                src=kampala, dst=gulu, bus_type='Non-AC', fare=22000,
                dd=dd, dh=6, dm=0, ah=12, am=0, seats=55,
                op=linkbus, policy=NORFND, am_str='USB Charging'))
            intercity.append(dict(
                bus_name=f'Northern Express KLA→GUL D{dd}',
                src=kampala, dst=gulu, bus_type='AC', fare=28000,
                dd=dd, dh=20, dm=0, ah=2, am=0, seats=45,
                op=eagle, policy=FREE24, am_str='AC,WiFi,USB Charging,Recliner Seats'))

        # ── Gulu → Kampala ───────────────────────────────────────
        for dd in [1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,46,49,
                   52,55,58,61,64,67,70,73,76,79,82,85,88,91,94,97,100]:
            intercity.append(dict(
                bus_name=f'Nile Star GUL→KLA D{dd}',
                src=gulu, dst=kampala, bus_type='Non-AC', fare=22000,
                dd=dd, dh=5, dm=0, ah=11, am=0, seats=55,
                op=linkbus, policy=NORFND, am_str='USB Charging'))

        # ── Kampala → Jinja ──────────────────────────────────────
        for dd in [1,2,3,4,5,8,9,10,11,12,15,16,17,18,19,22,23,24,
                   25,26,29,30,31,32,33,36,37,38,39,40,43,44,45,46,
                   47,50,51,52,53,54,57,58,59,60,61,64,65,66,67,68,
                   71,72,73,74,75,78,79,80,81,82,85,86,87,88,89,92,
                   93,94,95,96,99,100]:
            intercity.append(dict(
                bus_name=f'Kira Shuttle KLA→JNJ D{dd}',
                src=kampala, dst=jinja, bus_type='AC', fare=12000,
                dd=dd, dh=7, dm=0, ah=9, am=30, seats=30,
                op=postbus, policy=HALF6, am_str='AC,USB Charging'))

        # ── Jinja → Kampala ──────────────────────────────────────
        for dd in [1,3,5,8,10,12,15,17,19,22,24,26,29,31,33,36,38,
                   40,43,45,47,50,52,54,57,59,61,64,66,68,71,73,75,
                   78,80,82,85,87,89,92,94,96,99,100]:
            intercity.append(dict(
                bus_name=f'Kira Return JNJ→KLA D{dd}',
                src=jinja, dst=kampala, bus_type='AC', fare=12000,
                dd=dd, dh=16, dm=0, ah=18, am=30, seats=30,
                op=postbus, policy=HALF6, am_str='AC,USB Charging'))

        # ── Kampala → Mbale ──────────────────────────────────────
        for dd in [1,4,8,11,15,18,22,25,29,32,36,39,43,46,50,53,57,
                   60,64,67,71,74,78,81,85,88,92,95,99]:
            intercity.append(dict(
                bus_name=f'Mt. Elgon Coach KLA→MBL D{dd}',
                src=kampala, dst=mbale, bus_type='Sleeper', fare=35000,
                dd=dd, dh=20, dm=0, ah=dd+1, am=2, seats=40,
                op=ugexpress, policy=FREE48,
                am_str='AC,WiFi,USB Charging,Blanket & Pillow,Recliner Seats'))
            intercity.append(dict(
                bus_name=f'Elgon Express KLA→MBL D{dd}',
                src=kampala, dst=mbale, bus_type='AC', fare=28000,
                dd=dd, dh=7, dm=0, ah=dd, am=13, seats=45,
                op=horizon, policy=FREE24, am_str='AC,USB Charging'))

        # ── Mbale → Kampala ──────────────────────────────────────
        for dd in [1,4,8,11,15,18,22,25,29,32,36,39,43,46,50,53,57,
                   60,64,67,71,74,78,81,85,88,92,95,99]:
            intercity.append(dict(
                bus_name=f'Elgon Return MBL→KLA D{dd}',
                src=mbale, dst=kampala, bus_type='AC', fare=28000,
                dd=dd, dh=6, dm=0, ah=dd, am=12, seats=45,
                op=horizon, policy=FREE24, am_str='AC,USB Charging'))

        # ── Kampala → Kabale ─────────────────────────────────────
        for dd in [2,5,9,12,16,19,23,26,30,33,37,40,44,47,51,54,58,
                   61,65,68,72,75,79,82,86,89,93,96,100]:
            intercity.append(dict(
                bus_name=f'Kigezi Express KLA→KBL D{dd}',
                src=kampala, dst=kabale, bus_type='AC', fare=30000,
                dd=dd, dh=7, dm=0, ah=dd, am=14, seats=50,
                op=linkbus, policy=NORFND,
                am_str='AC,WiFi,Recliner Seats'))

        # ── Kabale → Kampala ─────────────────────────────────────
        for dd in [2,5,9,12,16,19,23,26,30,33,37,40,44,47,51,54,58,
                   61,65,68,72,75,79,82,86,89,93,96,100]:
            intercity.append(dict(
                bus_name=f'Kigezi Return KBL→KLA D{dd}',
                src=kabale, dst=kampala, bus_type='AC', fare=30000,
                dd=dd, dh=5, dm=0, ah=dd, am=12, seats=50,
                op=linkbus, policy=NORFND, am_str='AC,WiFi,Recliner Seats'))

        # ── Kampala → Fort Portal ────────────────────────────────
        for dd in [3,7,10,14,17,21,24,28,31,35,38,42,45,49,52,56,59,
                   63,66,70,73,77,80,84,87,91,94,98]:
            intercity.append(dict(
                bus_name=f'Rwenzori Coach KLA→FPT D{dd}',
                src=kampala, dst=fortprt, bus_type='AC', fare=28000,
                dd=dd, dh=7, dm=0, ah=dd, am=13, seats=48,
                op=eagle, policy=FREE24, am_str='AC,WiFi,USB Charging,Recliner Seats'))

        # ── Fort Portal → Kampala ────────────────────────────────
        for dd in [3,7,10,14,17,21,24,28,31,35,38,42,45,49,52,56,59,
                   63,66,70,73,77,80,84,87,91,94,98]:
            intercity.append(dict(
                bus_name=f'Rwenzori Return FPT→KLA D{dd}',
                src=fortprt, dst=kampala, bus_type='AC', fare=28000,
                dd=dd, dh=5, dm=30, ah=dd, am=11, seats=48,
                op=eagle, policy=FREE24, am_str='AC,WiFi,USB Charging'))

        # ── Kampala → Lira ───────────────────────────────────────
        for dd in [2,6,9,13,16,20,23,27,30,34,37,41,44,48,51,55,58,
                   62,65,69,72,76,79,83,86,90,93,97,100]:
            intercity.append(dict(
                bus_name=f'Lira Express KLA→LRA D{dd}',
                src=kampala, dst=lira, bus_type='Non-AC', fare=20000,
                dd=dd, dh=6, dm=0, ah=dd, am=12, seats=55,
                op=postbus, policy=NORFND, am_str='USB Charging'))

        # ── Lira → Kampala ───────────────────────────────────────
        for dd in [2,6,9,13,16,20,23,27,30,34,37,41,44,48,51,55,58,
                   62,65,69,72,76,79,83,86,90,93,97,100]:
            intercity.append(dict(
                bus_name=f'Lira Return LRA→KLA D{dd}',
                src=lira, dst=kampala, bus_type='Non-AC', fare=20000,
                dd=dd, dh=5, dm=0, ah=dd, am=11, seats=55,
                op=postbus, policy=NORFND, am_str='USB Charging'))

        # ── Kampala → Arua ───────────────────────────────────────
        for dd in [1,5,8,12,15,19,22,26,29,33,36,40,43,47,50,54,57,
                   61,64,68,71,75,78,82,85,89,92,96,99]:
            intercity.append(dict(
                bus_name=f'West Nile Coach KLA→ARU D{dd}',
                src=kampala, dst=arua, bus_type='Non-AC', fare=28000,
                dd=dd, dh=7, dm=0, ah=dd, am=16, seats=55,
                op=horizon, policy=FREE24, am_str='USB Charging,AC'))
            intercity.append(dict(
                bus_name=f'West Nile Sleeper KLA→ARU D{dd}',
                src=kampala, dst=arua, bus_type='Sleeper', fare=38000,
                dd=dd, dh=20, dm=0, ah=dd+1, am=5, seats=40,
                op=eagle, policy=FREE48,
                am_str='AC,WiFi,USB Charging,Blanket & Pillow,Recliner Seats'))

        # ── Arua → Kampala ───────────────────────────────────────
        for dd in [1,5,8,12,15,19,22,26,29,33,36,40,43,47,50,54,57,
                   61,64,68,71,75,78,82,85,89,92,96,99]:
            intercity.append(dict(
                bus_name=f'West Nile Return ARU→KLA D{dd}',
                src=arua, dst=kampala, bus_type='Non-AC', fare=28000,
                dd=dd, dh=5, dm=0, ah=dd, am=14, seats=55,
                op=horizon, policy=FREE24, am_str='USB Charging,AC'))

        # ── Kampala → Soroti ─────────────────────────────────────
        for dd in [3,7,11,14,18,21,25,28,32,35,39,42,46,49,53,56,60,
                   63,67,70,74,77,81,84,88,91,95,98]:
            intercity.append(dict(
                bus_name=f'Teso Coach KLA→SRT D{dd}',
                src=kampala, dst=soroti, bus_type='AC', fare=24000,
                dd=dd, dh=7, dm=0, ah=dd, am=13, seats=45,
                op=ugexpress, policy=FREE24, am_str='AC,USB Charging'))

        # ── Soroti → Kampala ─────────────────────────────────────
        for dd in [3,7,11,14,18,21,25,28,32,35,39,42,46,49,53,56,60,
                   63,67,70,74,77,81,84,88,91,95,98]:
            intercity.append(dict(
                bus_name=f'Teso Return SRT→KLA D{dd}',
                src=soroti, dst=kampala, bus_type='AC', fare=24000,
                dd=dd, dh=5, dm=0, ah=dd, am=11, seats=45,
                op=ugexpress, policy=FREE24, am_str='AC,USB Charging'))

        # ── Kampala → Hoima ──────────────────────────────────────
        for dd in [4,8,12,15,19,22,26,29,33,36,40,43,47,50,54,57,61,
                   64,68,71,75,78,82,85,89,92,96,99]:
            intercity.append(dict(
                bus_name=f'Oil City Express KLA→HMA D{dd}',
                src=kampala, dst=hoima, bus_type='AC', fare=22000,
                dd=dd, dh=7, dm=0, ah=dd, am=12, seats=48,
                op=linkbus, policy=FREE24, am_str='AC,USB Charging,WiFi'))

        # ── Hoima → Kampala ──────────────────────────────────────
        for dd in [4,8,12,15,19,22,26,29,33,36,40,43,47,50,54,57,61,
                   64,68,71,75,78,82,85,89,92,96,99]:
            intercity.append(dict(
                bus_name=f'Oil City Return HMA→KLA D{dd}',
                src=hoima, dst=kampala, bus_type='AC', fare=22000,
                dd=dd, dh=5, dm=30, ah=dd, am=10, seats=48,
                op=linkbus, policy=FREE24, am_str='AC,USB Charging,WiFi'))

        # ── Kampala → Masaka ─────────────────────────────────────
        for dd in [1,3,5,8,10,12,15,17,19,22,24,26,29,31,33,36,38,
                   40,43,45,47,50,52,54,57,59,61,64,66,68,71,73,75,
                   78,80,82,85,87,89,92,94,96,99]:
            intercity.append(dict(
                bus_name=f'Masaka Express KLA→MSK D{dd}',
                src=kampala, dst=masaka, bus_type='Non-AC', fare=15000,
                dd=dd, dh=7, dm=0, ah=dd, am=10, seats=55,
                op=postbus, policy=HALF6, am_str='USB Charging'))

        # ── Kampala → Tororo ─────────────────────────────────────
        for dd in [2,6,9,13,16,20,23,27,30,34,37,41,44,48,51,55,58,
                   62,65,69,72,76,79,83,86,90,93,97]:
            intercity.append(dict(
                bus_name=f'Border Coach KLA→TRO D{dd}',
                src=kampala, dst=tororo, bus_type='AC', fare=26000,
                dd=dd, dh=7, dm=0, ah=dd, am=13, seats=45,
                op=eagle, policy=FREE24, am_str='AC,USB Charging,WiFi'))

        # ── Kampala → Kasese ─────────────────────────────────────
        for dd in [3,7,11,15,19,22,26,30,33,37,41,44,48,52,55,59,63,
                   66,70,74,77,81,85,88,92,96,100]:
            intercity.append(dict(
                bus_name=f'Rwenzori Kasese KLA→KSS D{dd}',
                src=kampala, dst=kasese, bus_type='AC', fare=30000,
                dd=dd, dh=6, dm=30, ah=dd, am=14, seats=45,
                op=horizon, policy=FREE24,
                am_str='AC,WiFi,USB Charging,Recliner Seats'))

        # ── Insert all intercity trips ────────────────────────────
        for b in intercity:
            # handle next-day arrivals (ah value > 23 means dd+1)
            arr_day = b['dd']
            arr_hr  = b['am']   # field named 'am' holds arrival hour
            arr_min = 0         # field named 'am' in original schema
            # Some entries pass ah and am correctly; normalise here:
            if arr_hr > 23:
                arr_day += 1
                arr_hr  -= 24
            Bus.objects.get_or_create(
                bus_name=b['bus_name'],
                source=b['src'],
                destination=b['dst'],
                defaults=dict(
                    bus_type=b['bus_type'],
                    fare=b['fare'],
                    starting_time=dt(b['dd'], b['dh'], b['dm']),
                    arrival_time=dt(arr_day, arr_hr),
                    seats=b['seats'],
                    bus_operator=b['op'],
                    cancel_policy=b['policy'],
                    amenities=b['am_str'],
                    is_available=True,
                    status='Scheduled',
                )
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  Seeded {created} bus trips.'))

        # ── Banners ──────────────────────────────────────────────
        banners = [
            ('Explore Uganda by Bus',                'banner_images/2.jpg'),
            ('Book Smart, Travel Easy',              'banner_images/3.jpg'),
            ('CUU RouteLink — Your Transit Partner', 'banner_images/two.jpg'),
        ]
        for title, image in banners:
            Banner.objects.get_or_create(banner_title=title,
                                         defaults={'banner_image': image})
        self.stdout.write(self.style.SUCCESS('  Seeded banner images.'))
        self.stdout.write(self.style.SUCCESS('Done!'))
        self.stdout.write(self.style.WARNING('Admin: admin@cuuroute.ug / Admin@1234'))
