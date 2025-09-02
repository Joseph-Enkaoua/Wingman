# Generated manually to populate aircraft detail fields

from django.db import migrations

def populate_aircraft_details(apps, schema_editor):
    """Populate aircraft detail fields for existing flights"""
    Flight = apps.get_model('logbook', 'Flight')
    
    # Update all existing flights to have aircraft details populated
    for flight in Flight.objects.all():
        if flight.aircraft:
            flight.aircraft_manufacturer = flight.aircraft.manufacturer or ''
            flight.aircraft_type = flight.aircraft.type or ''
            flight.aircraft_engine_type = flight.aircraft.engine_type or 'SINGLE'
            flight.save()

def reverse_populate_aircraft_details(apps, schema_editor):
    """Reverse operation - clear aircraft detail fields"""
    Flight = apps.get_model('logbook', 'Flight')
    
    # Clear aircraft detail fields
    Flight.objects.all().update(
        aircraft_manufacturer='',
        aircraft_type='',
        aircraft_engine_type='SINGLE'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('logbook', '0008_add_aircraft_details_fields'),
    ]

    operations = [
        migrations.RunPython(
            populate_aircraft_details,
            reverse_populate_aircraft_details,
        ),
    ]
