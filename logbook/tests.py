from django.test import TestCase
from django.contrib.auth.models import User
from .models import Aircraft, Flight

# Create your tests here.

class AircraftEngineTypeTest(TestCase):
    """Test the new engine_type field functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testpilot',
            password='testpass123',
            first_name='John',
            last_name='Pilot'
        )
        
        self.single_engine_aircraft = Aircraft.objects.create(
            registration='F-GABC',
            type='Cessna 152',
            manufacturer='Cessna',
            year_manufactured=1978,
            engine_type='SINGLE',
            total_time=1000.0
        )
        
        self.multi_engine_aircraft = Aircraft.objects.create(
            registration='F-GDEF',
            type='Piper PA-34',
            manufacturer='Piper',
            year_manufactured=1985,
            engine_type='MULTI',
            total_time=1500.0
        )
    
    def test_aircraft_engine_type_choices(self):
        """Test that aircraft engine type choices work correctly"""
        self.assertEqual(self.single_engine_aircraft.engine_type, 'SINGLE')
        self.assertEqual(self.multi_engine_aircraft.engine_type, 'MULTI')
        self.assertEqual(self.single_engine_aircraft.get_engine_type_display(), 'Single Engine')
        self.assertEqual(self.multi_engine_aircraft.get_engine_type_display(), 'Multi Engine')
    
    def test_flight_inherits_engine_type(self):
        """Test that flights inherit engine type from aircraft"""
        flight = Flight.objects.create(
            pilot=self.user,
            date='2024-01-15',
            aircraft=self.single_engine_aircraft,
            departure_aerodrome='LFPB',
            arrival_aerodrome='LFPO',
            departure_time='09:00',
            arrival_time='10:00',
            total_time=1.0
        )
        
        # Test the properties
        self.assertEqual(flight.engine_type, 'SINGLE')
        self.assertTrue(flight.is_single_engine)
        self.assertFalse(flight.is_multi_engine)
        
        # Test with multi-engine aircraft
        multi_flight = Flight.objects.create(
            pilot=self.user,
            date='2024-01-16',
            aircraft=self.multi_engine_aircraft,
            departure_aerodrome='LFPO',
            arrival_aerodrome='LFPB',
            departure_time='14:00',
            arrival_time='15:00',
            total_time=1.0
        )
        
        self.assertEqual(multi_flight.engine_type, 'MULTI')
        self.assertFalse(multi_flight.is_single_engine)
        self.assertTrue(multi_flight.is_multi_engine)
