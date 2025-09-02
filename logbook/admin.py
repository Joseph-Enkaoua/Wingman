from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Flight, Aircraft, PilotProfile, CustomUser


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ['registration', 'type', 'manufacturer', 'year_manufactured', 'engine_type']
    list_filter = ['manufacturer', 'year_manufactured', 'engine_type']
    search_fields = ['registration', 'type', 'manufacturer']
    ordering = ['registration']


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'pilot_name', 'aircraft_registration', 'engine_type', 'departure_aerodrome', 
        'arrival_aerodrome', 'total_time', 'pilot_role', 'conditions'
    ]
    list_filter = [
        'date', 'pilot_role', 'conditions', 'flight_type', 'aircraft'
    ]
    search_fields = [
        'pilot__username', 'pilot__first_name', 'pilot__last_name',
        'aircraft__registration', 'aircraft_registration', 'departure_aerodrome', 'arrival_aerodrome'
    ]
    date_hierarchy = 'date'
    ordering = ['-date', '-departure_time']
    
    fieldsets = (
        ('Flight Information', {
            'fields': ('pilot', 'date', 'aircraft', 'departure_aerodrome', 'arrival_aerodrome')
        }),
        ('Time Details', {
            'fields': ('departure_time', 'arrival_time', 'total_time')
        }),
        ('Flight Conditions', {
            'fields': ('pilot_role', 'conditions', 'flight_type')
        }),
        ('Time Breakdown', {
            'fields': ('night_time', 'instrument_time', 'cross_country_time')
        }),
        ('Instructor Information', {
            'fields': ('instructor_name', 'instructor_rating')
        }),
        ('Landings', {
            'fields': ('landings_day', 'landings_night')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
    )
    
    def pilot_name(self, obj):
        return f"{obj.pilot.get_full_name()} ({obj.pilot.username})"
    pilot_name.short_description = 'Pilot'
    
    def aircraft_registration(self, obj):
        if obj.aircraft:
            return obj.aircraft.registration
        return f"{obj.aircraft_registration} (deleted)"
    aircraft_registration.short_description = 'Aircraft'
    
    def engine_type(self, obj):
        if obj.aircraft:
            return obj.aircraft.engine_type
        return 'N/A'
    engine_type.short_description = 'Engine Type'


@admin.register(PilotProfile)
class PilotProfileAdmin(admin.ModelAdmin):
    list_display = [
        'pilot_name', 'license_type', 'license_number', 'medical_class', 
        'medical_expiry', 'total_hours'
    ]
    list_filter = ['license_type', 'medical_class']
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'license_number', 'flight_school'
    ]
    ordering = ['user__last_name', 'user__first_name']
    
    fieldsets = (
        ('Pilot Information', {
            'fields': ('user', 'license_number', 'license_type')
        }),
        ('Medical Information', {
            'fields': ('medical_class', 'medical_expiry')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Flight School', {
            'fields': ('flight_school', 'instructor')
        }),

    )
    
    def pilot_name(self, obj):
        return f"{obj.user.get_full_name()} ({obj.user.username})"
    pilot_name.short_description = 'Pilot'
    
    def total_hours(self, obj):
        return f"{obj.total_flight_hours:.1f}"
    total_hours.short_description = 'Total Hours'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['username']
    
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets
    
    def get_queryset(self, request):
        """Return all users, not just the custom ones"""
        from django.contrib.auth.models import User
        return User.objects.all()
