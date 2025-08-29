from django.contrib import admin
from django.utils.html import format_html
from .models import Flight, Aircraft, PilotProfile


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ['registration', 'type', 'manufacturer', 'year_manufactured', 'total_time']
    list_filter = ['manufacturer', 'year_manufactured']
    search_fields = ['registration', 'type', 'manufacturer']
    ordering = ['registration']


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'pilot_name', 'aircraft_registration', 'departure_aerodrome', 
        'arrival_aerodrome', 'total_time', 'pilot_role', 'conditions'
    ]
    list_filter = [
        'date', 'pilot_role', 'conditions', 'flight_type', 'aircraft'
    ]
    search_fields = [
        'pilot__username', 'pilot__first_name', 'pilot__last_name',
        'aircraft__registration', 'departure_aerodrome', 'arrival_aerodrome'
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
        return obj.aircraft.registration
    aircraft_registration.short_description = 'Aircraft'


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
        ('Profile Picture', {
            'fields': ('profile_picture',)
        }),
    )
    
    def pilot_name(self, obj):
        return f"{obj.user.get_full_name()} ({obj.user.username})"
    pilot_name.short_description = 'Pilot'
    
    def total_hours(self, obj):
        return f"{obj.total_flight_hours:.1f}"
    total_hours.short_description = 'Total Hours'
