from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Aircraft(models.Model):
    """Model for aircraft registration and details"""
    registration = models.CharField(max_length=10, unique=True, help_text="Aircraft registration (e.g., F-GABC)")
    type = models.CharField(max_length=50, help_text="Aircraft type (e.g., Cessna 152)")
    manufacturer = models.CharField(max_length=50, blank=True)
    year_manufactured = models.IntegerField(blank=True, null=True)
    total_time = models.DecimalField(max_digits=8, decimal_places=1, default=0, help_text="Total aircraft time in hours")
    
    def __str__(self):
        return f"{self.registration} - {self.type}"


class Flight(models.Model):
    """Model for individual flight entries"""
    
    PILOT_ROLE_CHOICES = [
        ('PIC', 'Pilot in Command'),
        ('SIC', 'Second in Command'),
        ('DUAL', 'Dual Instruction'),
        ('TRAINER', 'Instructor Flight'),
        ('SOLO', 'Solo Flight'),
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
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    
    # Flight details
    departure_aerodrome = models.CharField(max_length=100)
    arrival_aerodrome = models.CharField(max_length=100)
    pilot_role = models.CharField(max_length=4, choices=PILOT_ROLE_CHOICES, default='PIC')
    conditions = models.CharField(max_length=4, choices=CONDITIONS_CHOICES, default='VFR')
    flight_type = models.CharField(max_length=15, choices=FLIGHT_TYPE_CHOICES, default='LOCAL')
    
    # Time tracking
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    total_time = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(Decimal('0.1'))])
    
    # Additional time breakdowns
    night_time = models.DecimalField(max_digits=4, decimal_places=1, default=0, validators=[MinValueValidator(Decimal('0.0'))])
    instrument_time = models.DecimalField(max_digits=4, decimal_places=1, default=0, validators=[MinValueValidator(Decimal('0.0'))])
    cross_country_time = models.DecimalField(max_digits=4, decimal_places=1, default=0, validators=[MinValueValidator(Decimal('0.0'))])
    
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
        return f"{self.date} - {self.aircraft.registration} - {self.departure_aerodrome} to {self.arrival_aerodrome}"
    
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
    
    # Profile picture
    profile_picture = models.ImageField(upload_to='pilot_profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.license_type}"
    
    @property
    def total_flight_hours(self):
        """Calculate total flight hours"""
        return sum(flight.total_time for flight in self.user.flights.all())
    
    @property
    def total_night_hours(self):
        """Calculate total night hours"""
        return sum(flight.night_time for flight in self.user.flights.all())
    
    @property
    def total_cross_country_hours(self):
        """Calculate total cross-country hours"""
        return sum(flight.cross_country_time for flight in self.user.flights.all())
    
    @property
    def total_instrument_hours(self):
        """Calculate total instrument hours"""
        return sum(flight.instrument_time for flight in self.user.flights.all())
    
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
