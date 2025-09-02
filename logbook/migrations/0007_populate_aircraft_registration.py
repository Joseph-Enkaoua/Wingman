# Generated manually to populate aircraft_registration field

from django.db import migrations

def populate_aircraft_registration(apps, schema_editor):
    """Populate aircraft_registration field for existing flights"""
    Flight = apps.get_model('logbook', 'Flight')
    
    # Update all existing flights to have aircraft_registration populated
    for flight in Flight.objects.all():
        if flight.aircraft:
            flight.aircraft_registration = flight.aircraft.registration
            flight.save()

def reverse_populate_aircraft_registration(apps, schema_editor):
    """Reverse operation - clear aircraft_registration field"""
    Flight = apps.get_model('logbook', 'Flight')
    
    # Clear aircraft_registration field
    Flight.objects.all().update(aircraft_registration='')

class Migration(migrations.Migration):

    dependencies = [
        ('logbook', '0006_add_aircraft_registration_field'),
    ]

    operations = [
        migrations.RunPython(
            populate_aircraft_registration,
            reverse_populate_aircraft_registration,
        ),
    ]
