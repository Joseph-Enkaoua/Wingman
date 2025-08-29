from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from logbook.models import Aircraft, Flight, PilotProfile
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Load sample data for the flight logbook application'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')

        # Create sample aircraft
        aircraft_data = [
            {'registration': 'F-GABC', 'type': 'Cessna 152', 'manufacturer': 'Cessna', 'year_manufactured': 1978},
            {'registration': 'F-GDEF', 'type': 'Piper PA-28', 'manufacturer': 'Piper', 'year_manufactured': 1982},
            {'registration': 'F-GHIJ', 'type': 'Diamond DA40', 'manufacturer': 'Diamond', 'year_manufactured': 2005},
        ]

        aircraft_list = []
        for data in aircraft_data:
            aircraft, created = Aircraft.objects.get_or_create(
                registration=data['registration'],
                defaults=data
            )
            aircraft_list.append(aircraft)
            if created:
                self.stdout.write(f'Created aircraft: {aircraft.registration}')

        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testpilot',
            defaults={
                'first_name': 'John',
                'last_name': 'Pilot',
                'email': 'john.pilot@example.com',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        # Create pilot profile
        pilot_profile, created = PilotProfile.objects.get_or_create(
            user=user,
            defaults={
                'license_number': 'FRA-123456',
                'license_type': 'PPL',
                'medical_class': 'Class 2',
                'medical_expiry': datetime.now().date() + timedelta(days=365),
                'phone': '+33 1 23 45 67 89',
                'address': '123 Aviation Street, Paris, France',
                'flight_school': 'Paris Flight Academy',
                'instructor': 'Captain Marie Dubois',
            }
        )
        if created:
            self.stdout.write(f'Created pilot profile for: {user.username}')

        # Create sample flights
        flight_data = [
            {
                'date': datetime.now().date() - timedelta(days=30),
                'departure_aerodrome': 'LFPB',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('09:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('10:30', '%H:%M').time(),
                'pilot_role': 'DUAL',
                'conditions': 'VFR',
                'flight_type': 'LOCAL',
                'night_time': 0,
                'instrument_time': 0,
                'cross_country_time': 0,
                'instructor_name': 'Captain Marie Dubois',
                'instructor_rating': 'CFI',
                'landings_day': 2,
                'landings_night': 0,
                'remarks': 'First cross-country flight. Great weather conditions.',
            },
            {
                'date': datetime.now().date() - timedelta(days=25),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFST',
                'departure_time': datetime.strptime('14:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('16:00', '%H:%M').time(),
                'pilot_role': 'PIC',
                'conditions': 'VFR',
                'flight_type': 'CROSS_COUNTRY',
                'night_time': 0,
                'instrument_time': 0,
                'cross_country_time': 2.0,
                'instructor_name': '',
                'instructor_rating': '',
                'landings_day': 1,
                'landings_night': 0,
                'remarks': 'Solo cross-country to Strasbourg. Beautiful flight over the countryside.',
            },
            {
                'date': datetime.now().date() - timedelta(days=20),
                'departure_aerodrome': 'LFST',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('18:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('19:30', '%H:%M').time(),
                'pilot_role': 'PIC',
                'conditions': 'VFR',
                'flight_type': 'CROSS_COUNTRY',
                'night_time': 0.5,
                'instrument_time': 0,
                'cross_country_time': 1.5,
                'instructor_name': '',
                'instructor_rating': '',
                'landings_day': 1,
                'landings_night': 1,
                'remarks': 'Return flight with some night time. Sunset was spectacular.',
            },
            {
                'date': datetime.now().date() - timedelta(days=15),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('10:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('11:30', '%H:%M').time(),
                'pilot_role': 'DUAL',
                'conditions': 'IFR',
                'flight_type': 'INSTRUMENT',
                'night_time': 0,
                'instrument_time': 1.5,
                'cross_country_time': 0,
                'instructor_name': 'Captain Marie Dubois',
                'instructor_rating': 'CFI',
                'landings_day': 3,
                'landings_night': 0,
                'remarks': 'Instrument training. Practiced approaches and holds.',
            },
            {
                'date': datetime.now().date() - timedelta(days=10),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('20:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('21:30', '%H:%M').time(),
                'pilot_role': 'DUAL',
                'conditions': 'VFR',
                'flight_type': 'NIGHT',
                'night_time': 1.5,
                'instrument_time': 0,
                'cross_country_time': 0,
                'instructor_name': 'Captain Marie Dubois',
                'instructor_rating': 'CFI',
                'landings_day': 0,
                'landings_night': 3,
                'remarks': 'Night flying training. Practiced night landings and navigation.',
            },
            {
                'date': datetime.now().date() - timedelta(days=5),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFML',
                'departure_time': datetime.strptime('12:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('14:30', '%H:%M').time(),
                'pilot_role': 'PIC',
                'conditions': 'VFR',
                'flight_type': 'CROSS_COUNTRY',
                'night_time': 0,
                'instrument_time': 0,
                'cross_country_time': 2.5,
                'instructor_name': '',
                'instructor_rating': '',
                'landings_day': 1,
                'landings_night': 0,
                'remarks': 'Long cross-country to Marseille. Beautiful coastal views.',
            },
            {
                'date': datetime.now().date() - timedelta(days=2),
                'departure_aerodrome': 'LFML',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('15:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('17:30', '%H:%M').time(),
                'pilot_role': 'PIC',
                'conditions': 'VFR',
                'flight_type': 'CROSS_COUNTRY',
                'night_time': 0,
                'instrument_time': 0,
                'cross_country_time': 2.5,
                'instructor_name': '',
                'instructor_rating': '',
                'landings_day': 1,
                'landings_night': 0,
                'remarks': 'Return flight from Marseille. Strong headwinds on the way back.',
            },
        ]

        for i, data in enumerate(flight_data):
            # Randomly select an aircraft
            aircraft = random.choice(aircraft_list)
            
            flight, created = Flight.objects.get_or_create(
                pilot=user,
                date=data['date'],
                aircraft=aircraft,
                departure_aerodrome=data['departure_aerodrome'],
                arrival_aerodrome=data['arrival_aerodrome'],
                defaults=data
            )
            if created:
                self.stdout.write(f'Created flight: {flight.date} - {flight.departure_aerodrome} to {flight.arrival_aerodrome}')

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data!')
        )
        self.stdout.write('Sample user credentials:')
        self.stdout.write('Username: testpilot')
        self.stdout.write('Password: testpass123')
