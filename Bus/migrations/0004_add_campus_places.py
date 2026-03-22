from django.db import migrations


CUU_CAMPUSES = [
    ('CUU Main Campus Nsambya',  0.296700, 32.583100),
    ('CUU Law Campus Acacia',    0.325000, 32.555000),
    ('CUU Mukono Campus',        0.353600, 32.755300),
]


def add_campus_places(apps, schema_editor):
    Place = apps.get_model('Bus', 'Place')
    for name, lat, lng in CUU_CAMPUSES:
        Place.objects.get_or_create(
            place_name=name,
            defaults={'latitude': lat, 'longitude': lng}
        )
    # Add CUU campus shuttle operator
    BusOperator = apps.get_model('Bus', 'BusOperator')
    BusOperator.objects.get_or_create(
        operator_name='CUU Campus Shuttle',
        defaults={'operator_contact': '+256700777888'}
    )
    BusOperator.objects.get_or_create(
        operator_name='Eagle Express Uganda',
        defaults={'operator_contact': '+256701234567'}
    )
    BusOperator.objects.get_or_create(
        operator_name='Horizon Bus Lines',
        defaults={'operator_contact': '+256702345678'}
    )


def remove_campus_places(apps, schema_editor):
    Place = apps.get_model('Bus', 'Place')
    for name, _, __ in CUU_CAMPUSES:
        Place.objects.filter(place_name=name).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('Bus', '0003_bus_amenities'),
    ]
    operations = [
        migrations.RunPython(add_campus_places, remove_campus_places),
    ]
