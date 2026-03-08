"""
Management command to seed sample bus data for development/demo.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from Bus.models import Place, BusOperator, Bus

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds sample bus data for development'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding sample data...')

        # Create superuser if not exists
        if not User.objects.filter(email='admin@cuuroute.ug').exists():
            User.objects.create_superuser(
                username='admin@cuuroute.ug',
                email='admin@cuuroute.ug',
                password='Admin@1234',
                first_name='System Admin',
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin@cuuroute.ug / Admin@1234'))

        # Get places
        try:
            kampala = Place.objects.get(place_name='Kampala')
            mbarara = Place.objects.get(place_name='Mbarara')
            gulu = Place.objects.get(place_name='Gulu')
            jinja = Place.objects.get(place_name='Jinja')
            mbale = Place.objects.get(place_name='Mbale')
            kabale = Place.objects.get(place_name='Kabale')
        except Place.DoesNotExist:
            self.stderr.write('Places not found — run migrate first.')
            return

        op1, _ = BusOperator.objects.get_or_create(operator_name='Uganda Bus Express', defaults={'operator_contact': '+256700111222'})
        op2, _ = BusOperator.objects.get_or_create(operator_name='Link Bus Services', defaults={'operator_contact': '+256700333444'})
        op3, _ = BusOperator.objects.get_or_create(operator_name='Post Bus Uganda', defaults={'operator_contact': '+256700555666'})

        now = timezone.now()

        buses = [
            dict(bus_name='Pearl Express', source=kampala, destination=mbarara, bus_type='AC',
                 fare=25000, starting_time=now + timedelta(hours=8), arrival_time=now + timedelta(hours=13),
                 seats=45, bus_operator=op1, cancel_policy='Free cancellation 24 hours before departure',
                 amenities='AC,WiFi,USB Charging,Recliner Seats'),
            dict(bus_name='Nile Star', source=kampala, destination=gulu, bus_type='Non-AC',
                 fare=20000, starting_time=now + timedelta(hours=6), arrival_time=now + timedelta(hours=12),
                 seats=55, bus_operator=op2, cancel_policy='No refund after booking',
                 amenities=''),
            dict(bus_name='Kira Shuttle', source=kampala, destination=jinja, bus_type='AC',
                 fare=12000, starting_time=now + timedelta(hours=3), arrival_time=now + timedelta(hours=5, minutes=30),
                 seats=30, bus_operator=op3, cancel_policy='50% refund if cancelled 6 hours before',
                 amenities='AC,USB Charging'),
            dict(bus_name='Mt. Elgon Coach', source=kampala, destination=mbale, bus_type='Sleeper',
                 fare=35000, starting_time=now + timedelta(hours=20), arrival_time=now + timedelta(hours=26),
                 seats=40, bus_operator=op1, cancel_policy='Free cancellation 48 hours before departure',
                 amenities='AC,WiFi,USB Charging,Blanket & Pillow,Recliner Seats'),
            dict(bus_name='Kigezi Express', source=kampala, destination=kabale, bus_type='AC',
                 fare=30000, starting_time=now + timedelta(hours=7), arrival_time=now + timedelta(hours=14),
                 seats=50, bus_operator=op2, cancel_policy='Non-refundable',
                 amenities='AC,WiFi,Recliner Seats'),
            dict(bus_name='Victoria Link', source=mbarara, destination=kampala, bus_type='Non-AC',
                 fare=22000, starting_time=now + timedelta(hours=5), arrival_time=now + timedelta(hours=10),
                 seats=55, bus_operator=op3, cancel_policy='Free cancellation 12 hours before',
                 amenities='USB Charging'),
        ]

        for b in buses:
            Bus.objects.get_or_create(bus_name=b['bus_name'], source=b['source'], defaults=b)

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(buses)} buses.'))
        self.stdout.write(self.style.SUCCESS('Done! Visit http://127.0.0.1:8000/ to see the result.'))
        self.stdout.write(self.style.WARNING('Admin: admin@cuuroute.ug / Admin@1234'))
