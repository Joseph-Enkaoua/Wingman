from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class Aircraft(models.Model):
    """Model for aircraft registration and details"""
    
    ENGINE_TYPE_CHOICES = [
        ('SINGLE', 'Single Engine'),
        ('MULTI', 'Multi Engine'),
    ]
    
    registration = models.CharField(max_length=10, unique=True, help_text="Aircraft registration (e.g., F-GABC)")
    type = models.CharField(max_length=50, help_text="Aircraft type (e.g., Cessna 152)")
    manufacturer = models.CharField(max_length=50, blank=True)
    year_manufactured = models.IntegerField(blank=True, null=True)
    engine_type = models.CharField(max_length=6, choices=ENGINE_TYPE_CHOICES, default='SINGLE', help_text="Number of engines")
    
    class Meta:
        ordering = ['registration']
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"
    
    def __str__(self):
        return f"{self.registration} - {self.type}"


class Flight(models.Model):
    """Model for individual flight entries"""
    
    PILOT_ROLE_CHOICES = [
        ('PIC', 'Pilot in Command'),
        ('SIC', 'Second in Command'),
        ('SOLO', 'Solo Flight'),
        ('DUAL', 'Dual Instruction Received'),
        ('INSTR', 'Flight Instruction Given'),
        ('SP', 'Safety Pilot'),
        ('SIM', 'Simulator'),
    ]

    CONDITIONS_CHOICES = [
        ('VFR', 'Visual Flight Rules'),
        ('IFR', 'Instrument Flight Rules'),
        ('SVFR', 'Special VFR'),
    ]
    
    FLIGHT_TYPE_CHOICES = [
        ('LOCAL', 'Local Flight'),
        ('CROSS_COUNTRY', 'Cross Country'),
        ('NIGHT', 'Night Flight'),
        ('INSTRUMENT', 'Instrument Flight'),
        ('TOWER', 'Tower Controlled'),
        ('UNCONTROLLED', 'Uncontrolled Airspace'),
    ]
    
    # Basic flight information
    pilot = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flights')
    date = models.DateField()
    aircraft = models.ForeignKey(Aircraft, on_delete=models.SET_NULL, null=True, blank=True)
    aircraft_registration = models.CharField(max_length=10, blank=True, help_text="Aircraft registration (preserved when aircraft is deleted)")
    aircraft_manufacturer = models.CharField(max_length=50, blank=True, help_text="Aircraft manufacturer (preserved when aircraft is deleted)")
    aircraft_type = models.CharField(max_length=50, blank=True, help_text="Aircraft type (preserved when aircraft is deleted)")
    aircraft_engine_type = models.CharField(max_length=6, choices=[('SINGLE', 'Single Engine'), ('MULTI', 'Multi Engine')], blank=True, help_text="Aircraft engine type (preserved when aircraft is deleted)")
    
    # Flight details
    departure_aerodrome = models.CharField(max_length=100)
    arrival_aerodrome = models.CharField(max_length=100)
    pilot_role = models.CharField(max_length=5, choices=PILOT_ROLE_CHOICES, default='PIC')
    conditions = models.CharField(max_length=4, choices=CONDITIONS_CHOICES, default='VFR')
    flight_type = models.CharField(max_length=15, choices=FLIGHT_TYPE_CHOICES, default='LOCAL')
    
    # Time tracking
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    total_time = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(Decimal('0.1'))])
    
    # Additional time breakdowns
    night_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Night time in minutes")
    instrument_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Instrument time in minutes")
    cross_country_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Cross country time in minutes")
    
    # Instructor information
    instructor_name = models.CharField(max_length=100, blank=True)
    instructor_rating = models.CharField(max_length=50, blank=True)
    
    # Flight details
    remarks = models.TextField(blank=True)
    landings_day = models.PositiveIntegerField(default=0)
    landings_night = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-departure_time']
        verbose_name = "Flight"
        verbose_name_plural = "Flights"
    
    def __str__(self):
        aircraft_info = self.aircraft.registration if self.aircraft else self.aircraft_registration
        return f"{self.date} - {aircraft_info} - {self.departure_aerodrome} to {self.arrival_aerodrome}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total time if not provided
        if not self.total_time:
            from datetime import datetime, timedelta
            if self.departure_time and self.arrival_time:
                # Calculate time difference
                departure_dt = datetime.combine(self.date, self.departure_time)
                arrival_dt = datetime.combine(self.date, self.arrival_time)
                
                # Handle overnight flights
                if arrival_dt < departure_dt:
                    arrival_dt += timedelta(days=1)
                
                time_diff = arrival_dt - departure_dt
                self.total_time = Decimal(str(time_diff.total_seconds() / 3600)).quantize(Decimal('0.1'))
        
        # Auto-populate aircraft details from aircraft reference
        if self.aircraft:
            if not self.aircraft_registration:
                self.aircraft_registration = self.aircraft.registration
            if not self.aircraft_manufacturer:
                self.aircraft_manufacturer = self.aircraft.manufacturer
            if not self.aircraft_type:
                self.aircraft_type = self.aircraft.type
            if not self.aircraft_engine_type:
                self.aircraft_engine_type = self.aircraft.engine_type
        
        super().save(*args, **kwargs)
    
    @property
    def is_cross_country(self):
        """Determine if flight is cross-country based on distance or time"""
        return self.flight_type == 'CROSS_COUNTRY' or self.cross_country_time > 0
    
    @property
    def is_night_flight(self):
        """Determine if flight includes night time"""
        return self.night_time > 0
    
    @property
    def is_dual_instruction(self):
        """Determine if flight was dual instruction"""
        return self.pilot_role == 'DUAL' or bool(self.instructor_name)
    
    @property
    def engine_type(self):
        """Get the engine type from the associated aircraft"""
        if self.aircraft:
            return self.aircraft.engine_type
        return self.aircraft_engine_type
    
    @property
    def is_single_engine(self):
        """Determine if the aircraft used is single engine"""
        if self.aircraft:
            return self.aircraft.engine_type == 'SINGLE'
        return self.aircraft_engine_type == 'SINGLE'
    
    @property
    def is_multi_engine(self):
        """Determine if the aircraft used is multi-engine"""
        if self.aircraft:
            return self.aircraft.engine_type == 'MULTI'
        return self.aircraft_engine_type == 'MULTI'


class PilotProfile(models.Model):
    """Extended profile for pilots with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pilot_profile')
    
    # Pilot information
    license_number = models.CharField(max_length=50, blank=True)
    license_type = models.CharField(max_length=50, blank=True, help_text="e.g., PPL, CPL, ATPL")
    medical_class = models.CharField(max_length=10, blank=True, help_text="e.g., Class 1, Class 2")
    medical_expiry = models.DateField(blank=True, null=True)
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Flight school information
    flight_school = models.CharField(max_length=100, blank=True)
    instructor = models.CharField(max_length=100, blank=True)
    

    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.license_type}"
    
    @property
    def total_flight_hours(self):
        """Calculate total flight hours"""
        return sum(flight.total_time for flight in self.user.flights.all())
    
    @property
    def total_night_hours(self):
        """Calculate total night hours (convert minutes to hours)"""
        total_minutes = sum(flight.night_time for flight in self.user.flights.all())
        return total_minutes / 60
    
    @property
    def total_cross_country_hours(self):
        """Calculate total cross-country hours (convert minutes to hours)"""
        total_minutes = sum(flight.cross_country_time for flight in self.user.flights.all())
        return total_minutes / 60
    
    @property
    def total_instrument_hours(self):
        """Calculate total instrument hours (convert minutes to hours)"""
        total_minutes = sum(flight.instrument_time for flight in self.user.flights.all())
        return total_minutes / 60
    
    @property
    def total_dual_hours(self):
        """Calculate total dual instruction hours"""
        return sum(flight.total_time for flight in self.user.flights.all() 
                  if flight.pilot_role == 'DUAL' or flight.instructor_name)
    
    @property
    def total_solo_hours(self):
        """Calculate total solo hours"""
        return sum(flight.total_time for flight in self.user.flights.all() 
                  if flight.pilot_role == 'SOLO')
    
    @property
    def total_pic_hours(self):
        """Calculate total PIC hours"""
        return sum(flight.total_time for flight in self.user.flights.all() 
                  if flight.pilot_role == 'PIC')


class CustomUser(User):
    """Custom user model with email uniqueness constraint"""
    
    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def clean(self):
        """Validate email uniqueness"""
        super().clean()
        if self.email:
            # Check if another user has this email (excluding current user)
            if User.objects.filter(email=self.email).exclude(pk=self.pk).exists():
                raise ValidationError("A user with this email already exists.")
    
    def save(self, *args, **kwargs):
        """Ensure email uniqueness before saving"""
        self.clean()
        super().save(*args, **kwargs)
