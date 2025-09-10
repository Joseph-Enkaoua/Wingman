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
    
    # Time tracking
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    total_time = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(Decimal('0.1'))])
    
    # New time breakdowns for the refactored structure
    single_engine_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Single engine time in minutes")
    multi_engine_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Multi engine time in minutes")
    multi_pilot_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Multi-pilot flight time in minutes")
    day_landings = models.PositiveIntegerField(default=0, help_text="Number of day landings")
    night_landings = models.PositiveIntegerField(default=0, help_text="Number of night landings")
    ifr_approaches = models.PositiveIntegerField(default=0, verbose_name="IFR Approaches", help_text="Number of IFR approaches")
    night_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Night time in minutes")
    ifr_time = models.IntegerField(default=0, verbose_name="IFR Time", validators=[MinValueValidator(0)], help_text="IFR time in minutes")
    pic_time = models.IntegerField(default=0, verbose_name="PIC Time", validators=[MinValueValidator(0)], help_text="PIC time in minutes")
    copilot_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Co-pilot time in minutes")
    double_command_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Double command time in minutes")
    instructor_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Instructor time in minutes")
    
    # Simulator fields
    simulator_type = models.CharField(max_length=100, blank=True, help_text="Type of simulator used")
    simulator_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Simulator time in minutes")
    
    # Legacy fields for backward compatibility (will be removed in future migration)
    instrument_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Instrument time in minutes (legacy)")
    cross_country_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Cross country time in minutes (legacy)")
    landings_day = models.PositiveIntegerField(default=0)  # Legacy field
    landings_night = models.PositiveIntegerField(default=0)  # Legacy field
    
    # Flight details
    remarks = models.TextField(blank=True)
    
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
                # Calculate in minutes first for accuracy, then convert to hours
                total_minutes = time_diff.total_seconds() / 60
                # Round to the nearest minute, then convert to hours with more precision
                total_minutes_rounded = round(total_minutes)
                self.total_time = Decimal(str(total_minutes_rounded / 60)).quantize(Decimal('0.01'))
        
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
            
            # Auto-populate engine time based on aircraft type
            # Always update engine time since users can no longer set it manually
            if self.aircraft.engine_type == 'SINGLE':
                self.single_engine_time = int(self.total_time * 60) if self.total_time else 0
                self.multi_engine_time = 0  # Reset multi-engine time for single-engine aircraft
            elif self.aircraft.engine_type == 'MULTI':
                self.multi_engine_time = int(self.total_time * 60) if self.total_time else 0
                self.single_engine_time = 0  # Reset single-engine time for multi-engine aircraft
        else:
            # No aircraft (simulator flights) - reset both engine times
            self.single_engine_time = 0
            self.multi_engine_time = 0
        
        super().save(*args, **kwargs)
    
    @property
    def is_cross_country(self):
        """Determine if flight is cross-country based on distance or time"""
        # For backward compatibility, check legacy field first
        if hasattr(self, 'cross_country_time') and self.cross_country_time > 0:
            return True
        # New logic: consider it cross-country if departure and arrival are different
        return self.departure_aerodrome != self.arrival_aerodrome
    
    @property
    def is_night_flight(self):
        """Determine if flight includes night time"""
        return self.night_time > 0
    
    @property
    def is_dual_instruction(self):
        """Determine if flight was dual instruction"""
        return self.instructor_time > 0
    
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
    
    def get_pilot_role_display(self):
        """Determine pilot role based on time fields"""
        if self.pic_time > 0:
            return 'PIC'
        elif self.copilot_time > 0:
            return 'SIC'
        elif self.instructor_time > 0:
            return 'DUAL'
        elif self.multi_pilot_time > 0:
            return 'MULTI'
        elif self.simulator_time > 0:
            return 'SIM'
        else:
            return 'PIC'  # Default to PIC if no specific role is set

    @property
    def exact_flight_minutes(self):
        """Calculate exact flight time in minutes for accurate calculations"""
        if self.departure_time and self.arrival_time:
            from datetime import datetime, timedelta
            departure_dt = datetime.combine(self.date, self.departure_time)
            arrival_dt = datetime.combine(self.date, self.arrival_time)
            
            # Handle overnight flights
            if arrival_dt < departure_dt:
                arrival_dt += timedelta(days=1)
            
            time_diff = arrival_dt - departure_dt
            return int(time_diff.total_seconds() / 60)
        return int(self.total_time * 60) if self.total_time else 0
    
    def recalculate_total_time(self):
        """Recalculate and update total_time field with exact calculation"""
        if self.departure_time and self.arrival_time:
            exact_minutes = self.exact_flight_minutes
            self.total_time = Decimal(str(exact_minutes / 60)).quantize(Decimal('0.01'))
            self.save(update_fields=['total_time'])
            return True
        return False


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
        """Calculate total flight hours accurately by converting to minutes first"""
        total_minutes = sum(flight.exact_flight_minutes for flight in self.user.flights.all())
        return total_minutes / 60
    
    @property
    def total_night_hours(self):
        """Calculate total night hours (convert minutes to hours)"""
        total_minutes = sum(flight.night_time for flight in self.user.flights.all())
        return total_minutes / 60
    
    @property
    def total_cross_country_hours(self):
        """Calculate total cross-country hours based on flights with different departure/arrival aerodromes"""
        total_minutes = 0
        for flight in self.user.flights.all():
            if flight.is_cross_country:
                total_minutes += flight.exact_flight_minutes
        return total_minutes / 60
    
    @property
    def total_instrument_hours(self):
        """Calculate total IFR hours (convert minutes to hours)"""
        total_minutes = sum(flight.ifr_time for flight in self.user.flights.all())
        return total_minutes / 60
    
    @property
    def total_dual_hours(self):
        """Calculate total dual instruction hours"""
        return sum(flight.instructor_time / 60 for flight in self.user.flights.all() 
                  if flight.instructor_time > 0)
    
    @property
    def total_solo_hours(self):
        """Calculate total solo hours"""
        return sum(flight.pic_time / 60 for flight in self.user.flights.all() 
                  if flight.pic_time > 0)
    
    @property
    def total_pic_hours(self):
        """Calculate total PIC hours"""
        return sum(flight.pic_time / 60 for flight in self.user.flights.all() 
                  if flight.pic_time > 0)


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
                raise ValidationError("This email cannot be used to register.")
    
    def save(self, *args, **kwargs):
        """Ensure email uniqueness before saving"""
        self.clean()
        super().save(*args, **kwargs)
