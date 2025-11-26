from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from logbook.models import Aircraft, Flight, PilotProfile
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Set up demo user with sample data for demo mode'

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo user...')

        # Create sample aircraft
        aircraft_data = [
            {'registration': 'F-GABC', 'type': 'Cessna 152', 'manufacturer': 'Cessna', 'year_manufactured': 1978, 'engine_type': 'SINGLE'},
            {'registration': 'F-GDEF', 'type': 'Piper PA-28', 'manufacturer': 'Piper', 'year_manufactured': 1982, 'engine_type': 'SINGLE'},
            {'registration': 'F-GHIJ', 'type': 'Diamond DA40', 'manufacturer': 'Diamond', 'year_manufactured': 2005, 'engine_type': 'SINGLE'},
            {'registration': 'N123AB', 'type': 'Cessna 172', 'manufacturer': 'Cessna', 'year_manufactured': 2010, 'engine_type': 'SINGLE'},
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

        # Get or create demo user
        demo_user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Pilot',
                'email': 'demo@wingman.cyou',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if created:
            demo_user.set_password('demo_password_secure_12345')
            demo_user.save()
            self.stdout.write(f'Created demo user: {demo_user.username}')
        else:
            self.stdout.write(f'Demo user already exists: {demo_user.username}')

        # Create or update pilot profile
        pilot_profile, created = PilotProfile.objects.get_or_create(
            user=demo_user,
            defaults={
                'license_number': 'DEMO-123456',
                'license_type': 'PPL',
                'medical_class': 'Class 2',
                'medical_expiry': datetime.now().date() + timedelta(days=365),
                'phone': '+1 555 123 4567',
                'address': '123 Aviation Way, Demo City',
                'flight_school': 'Demo Flight Academy',
                'instructor': 'Captain Demo Instructor',
            }
        )
        if created:
            self.stdout.write(f'Created pilot profile for: {demo_user.username}')
        else:
            # Update existing profile
            pilot_profile.license_number = 'DEMO-123456'
            pilot_profile.license_type = 'PPL'
            pilot_profile.medical_class = 'Class 2'
            pilot_profile.medical_expiry = datetime.now().date() + timedelta(days=365)
            pilot_profile.save()
            self.stdout.write(f'Updated pilot profile for: {demo_user.username}')

        # Delete existing demo flights to avoid duplicates
        Flight.objects.filter(pilot=demo_user).delete()
        self.stdout.write('Cleared existing demo flights')

        # Create sample flights with proper field names
        flight_data = [
            {
                'date': datetime.now().date() - timedelta(days=30),
                'departure_aerodrome': 'LFPB',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('09:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('10:30', '%H:%M').time(),
                'pic_time': 0,
                'instructor_time': 90,  # 1.5 hours in minutes
                'single_engine_time': 90,
                'night_time': 0,
                'ifr_time': 0,
                'day_landings': 2,
                'night_landings': 0,
                'ifr_approaches': 0,
                'remarks': 'First cross-country flight. Great weather conditions.',
            },
            {
                'date': datetime.now().date() - timedelta(days=25),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFST',
                'departure_time': datetime.strptime('14:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('16:00', '%H:%M').time(),
                'pic_time': 120,  # 2 hours in minutes
                'instructor_time': 0,
                'single_engine_time': 120,
                'night_time': 0,
                'ifr_time': 0,
                'day_landings': 1,
                'night_landings': 0,
                'ifr_approaches': 0,
                'remarks': 'Solo cross-country to Strasbourg. Beautiful flight over the countryside.',
            },
            {
                'date': datetime.now().date() - timedelta(days=20),
                'departure_aerodrome': 'LFST',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('18:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('19:30', '%H:%M').time(),
                'pic_time': 90,
                'instructor_time': 0,
                'single_engine_time': 90,
                'night_time': 30,  # 0.5 hours in minutes
                'ifr_time': 0,
                'day_landings': 1,
                'night_landings': 1,
                'ifr_approaches': 0,
                'remarks': 'Return flight with some night time. Sunset was spectacular.',
            },
            {
                'date': datetime.now().date() - timedelta(days=15),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('10:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('11:30', '%H:%M').time(),
                'pic_time': 0,
                'instructor_time': 90,
                'single_engine_time': 90,
                'night_time': 0,
                'ifr_time': 90,  # 1.5 hours in minutes
                'day_landings': 3,
                'night_landings': 0,
                'ifr_approaches': 3,
                'remarks': 'Instrument training. Practiced approaches and holds.',
            },
            {
                'date': datetime.now().date() - timedelta(days=10),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('20:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('21:30', '%H:%M').time(),
                'pic_time': 0,
                'instructor_time': 90,
                'single_engine_time': 90,
                'night_time': 90,  # 1.5 hours in minutes
                'ifr_time': 0,
                'day_landings': 0,
                'night_landings': 3,
                'ifr_approaches': 0,
                'remarks': 'Night flying training. Practiced night landings and navigation.',
            },
            {
                'date': datetime.now().date() - timedelta(days=5),
                'departure_aerodrome': 'LFPO',
                'arrival_aerodrome': 'LFML',
                'departure_time': datetime.strptime('12:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('14:30', '%H:%M').time(),
                'pic_time': 150,  # 2.5 hours in minutes
                'instructor_time': 0,
                'single_engine_time': 150,
                'night_time': 0,
                'ifr_time': 0,
                'day_landings': 1,
                'night_landings': 0,
                'ifr_approaches': 0,
                'remarks': 'Long cross-country to Marseille. Beautiful coastal views.',
            },
            {
                'date': datetime.now().date() - timedelta(days=2),
                'departure_aerodrome': 'LFML',
                'arrival_aerodrome': 'LFPO',
                'departure_time': datetime.strptime('15:00', '%H:%M').time(),
                'arrival_time': datetime.strptime('17:30', '%H:%M').time(),
                'pic_time': 150,
                'instructor_time': 0,
                'single_engine_time': 150,
                'night_time': 0,
                'ifr_time': 0,
                'day_landings': 1,
                'night_landings': 0,
                'ifr_approaches': 0,
                'remarks': 'Return flight from Marseille. Strong headwinds on the way back.',
            },
        ]

        for data in flight_data:
            # Randomly select an aircraft
            aircraft = random.choice(aircraft_list)
            
            flight = Flight.objects.create(
                pilot=demo_user,
                aircraft=aircraft,
                **data
            )
            self.stdout.write(f'Created flight: {flight.date} - {flight.departure_aerodrome} to {flight.arrival_aerodrome}')

        self.stdout.write(
            self.style.SUCCESS('Successfully set up demo user with sample data!')
        )
        self.stdout.write('Demo user credentials:')
        self.stdout.write('Username: demo')
        self.stdout.write('Password: (auto-login via demo mode)')

