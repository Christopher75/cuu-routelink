from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bus', '0002_populate_places'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='amenities',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
