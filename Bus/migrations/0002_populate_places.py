from django.db import migrations
import uuid


UGANDA_CITIES = [
    ('Kampala',    0.316667, 32.583333),
    ('Entebbe',    0.060000, 32.460000),
    ('Jinja',      0.425000, 33.200000),
    ('Mbarara',   -0.607800, 30.654700),
    ('Gulu',       2.774390, 32.299000),
    ('Mbale',      1.075100, 34.175900),
    ('Fort Portal', 0.671000, 30.275000),
    ('Kabale',    -1.250000, 29.990000),
    ('Masaka',    -0.340000, 31.736000),
    ('Lira',       2.249600, 32.899900),
    ('Arua',       3.020000, 30.910000),
    ('Soroti',     1.714000, 33.611000),
    ('Tororo',     0.692700, 34.181500),
    ('Kasese',     0.183000, 30.083000),
    ('Hoima',      1.433000, 31.350000),
]


def populate_places(apps, schema_editor):
    Place = apps.get_model('Bus', 'Place')
    BusOperator = apps.get_model('Bus', 'BusOperator')
    for name, lat, lng in UGANDA_CITIES:
        Place.objects.get_or_create(
            place_name=name,
            defaults={'latitude': lat, 'longitude': lng}
        )
    # Default operators
    BusOperator.objects.get_or_create(
        operator_name='Uganda Bus Express',
        defaults={'operator_contact': '+256700111222'}
    )
    BusOperator.objects.get_or_create(
        operator_name='Link Bus Services',
        defaults={'operator_contact': '+256700333444'}
    )
    BusOperator.objects.get_or_create(
        operator_name='Post Bus Uganda',
        defaults={'operator_contact': '+256700555666'}
    )


def reverse_places(apps, schema_editor):
    Place = apps.get_model('Bus', 'Place')
    Place.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('Bus', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_places, reverse_places),
    ]
