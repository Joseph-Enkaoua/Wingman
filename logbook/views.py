from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Sum, Count, Case, When, Value, CharField
from django.utils import timezone
from datetime import datetime
import json
import calendar
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.views import View
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Flight, Aircraft, PilotProfile
from .forms import FlightForm, AircraftForm, PilotProfileForm, UserRegistrationForm, FlightSearchForm, PasswordResetRequestForm, SetPasswordForm
from .decorators import adaptive_ratelimit, user_ratelimit
from collections import defaultdict

import logging
import resend
import os

# Set up logger for this module
logger = logging.getLogger(__name__)

resend.api_key = os.getenv('RESEND_API_KEY')

def get_client_ip(request):
    """Get client IP for logging purposes"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calculate_aircraft_usage_accurate(flights_queryset, limit=None):
    """
    Calculate aircraft usage with exact flight time calculations for accuracy.
    Returns a list of dictionaries with aircraft usage data.
    """
    # Group flights by aircraft registration
    aircraft_totals = defaultdict(lambda: {
        'registration': '',
        'manufacturer': '',
        'type': '',
        'total_hours': 0,
        'flight_count': 0
    })
    
    for flight in flights_queryset:
        # Determine aircraft registration
        if flight.aircraft:
            registration = flight.aircraft.registration
            manufacturer = flight.aircraft.manufacturer
            aircraft_type = flight.aircraft.type
        elif flight.aircraft_registration:
            registration = flight.aircraft_registration
            manufacturer = flight.aircraft_manufacturer
            aircraft_type = flight.aircraft_type
        else:
            registration = 'SIM'
            manufacturer = 'Simulator'
            aircraft_type = 'SIM'
        
        # Add to totals using exact calculation
        aircraft_totals[registration]['registration'] = registration
        aircraft_totals[registration]['manufacturer'] = manufacturer or ''
        aircraft_totals[registration]['type'] = aircraft_type or ''
        aircraft_totals[registration]['total_hours'] += flight.exact_flight_minutes / 60
        aircraft_totals[registration]['flight_count'] += 1
    
    # Convert to list and sort by total hours
    result = list(aircraft_totals.values())
    result.sort(key=lambda x: x['total_hours'], reverse=True)
    
    return result[:limit] if limit else result


class CustomLoginView(View):
    """Custom login view with rate limiting and enhanced security"""
    template_name = 'logbook/login.html'
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=False))
    @method_decorator(ratelimit(key='ip', rate='20/h', method='POST', block=False))
    def post(self, request, *args, **kwargs):
        # Check rate limiting and show messages instead of blocking
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            logger.warning(f'Rate limit exceeded for login attempts from IP: {get_client_ip(request)}')
            messages.error(request, 'Too many login attempts. Please wait a few minutes before trying again for security reasons.')
            return self.get(request, *args, **kwargs)
        
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Log successful login
                logger.info(f'Successful login for user: {username} from IP: {get_client_ip(request)}')
                return redirect('dashboard')
            else:
                # Authentication failed - this will trigger the user_login_failed signal
                # so we don't need to log it here to avoid duplication
                messages.error(request, 'Invalid username or password.')
        else:
            # Only log actual form validation errors, not authentication errors
            # Authentication errors are handled by the user_login_failed signal
            if form.errors and not form.errors.get('__all__'):
                # This is a real form validation error (empty fields, etc.)
                username_attempt = request.POST.get('username', 'unknown')
                logger.warning(f'*** INVALID LOGIN FORM *** for username: {username_attempt} from IP: {get_client_ip(request)} - Form errors: {form.errors}')
            
            messages.error(request, 'Invalid username or password.')
        
        return self.get(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})


@ratelimit(key='ip', rate='3/h', method='POST', block=False)
def register_view(request):
    """Registration view with rate limiting"""
    if request.method == 'POST':
        # Check rate limiting and show messages instead of blocking
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            logger.warning(f'Registration rate limit exceeded from IP: {get_client_ip(request)}')
            messages.error(request, 'Too many registration attempts. Please wait a few minutes before trying again for security reasons.')
            form = UserRegistrationForm()
            return render(request, 'logbook/register.html', {'form': form})
            
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f'Successful registration for user: {user.username} from IP: {get_client_ip(request)}')
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            # Log failed registration attempt
            username_attempt = request.POST.get('username', 'unknown')
            logger.warning(f'Failed registration attempt for username: {username_attempt} from IP: {get_client_ip(request)}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'logbook/register.html', {'form': form})


def logout_view(request):
    """Simple logout view that clears session and redirects to login"""
    from django.contrib.auth import logout
    from django.contrib import messages
    
    # Clear all messages before logout to prevent them from appearing on login page
    storage = messages.get_messages(request)
    storage.used = True
    
    # Also clear any existing messages in the session
    if hasattr(request, 'session'):
        request.session['_messages'] = []
    
    logout(request)
    return redirect('/login/')


@login_required
def dashboard(request):
    """Dashboard view with flight statistics and charts"""
    user = request.user
    
    # Get pilot profile or create one
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    # Get recent flights
    recent_flights = Flight.objects.filter(pilot=user).order_by('-date', '-departure_time')[:5]
    
    # Calculate statistics
    total_flights = Flight.objects.filter(pilot=user).count()
    total_hours = pilot_profile.total_flight_hours
    total_night_hours = pilot_profile.total_night_hours
    total_cross_country_hours = pilot_profile.total_cross_country_hours
    total_instrument_hours = pilot_profile.total_instrument_hours
    total_dual_hours = pilot_profile.total_dual_hours
    total_solo_hours = pilot_profile.total_solo_hours
    total_pic_hours = pilot_profile.total_pic_hours
    
    # Calculate average flight time
    avg_flight_time = 0
    if total_flights > 0:
        avg_flight_time = total_hours / total_flights
    
    # Get most used aircraft using accurate calculation
    most_used_aircraft = "N/A"
    if total_flights > 0:
        aircraft_usage_accurate = calculate_aircraft_usage_accurate(Flight.objects.filter(pilot=user), limit=1)
        if aircraft_usage_accurate:
            most_used_aircraft = aircraft_usage_accurate[0]['registration']
    
    # Calculate landing statistics
    landing_stats = Flight.objects.filter(pilot=user).aggregate(
        total_day_landings=Sum('day_landings'),
        total_night_landings=Sum('night_landings')
    )
    total_day_landings = landing_stats['total_day_landings'] or 0
    total_night_landings = landing_stats['total_night_landings'] or 0
    
    # Calculate IFR approaches
    total_ifr_approaches = Flight.objects.filter(pilot=user).aggregate(
        total=Sum('ifr_approaches')
    )['total'] or 0
    
    # Monthly flight hours for the last 12 months
    monthly_hours = []
    
    # Get current date
    current_date = timezone.now().date()
    
    for i in range(12):
        # Calculate the month we're looking at
        if i == 0:
            # Current month
            year = current_date.year
            month = current_date.month
        else:
            # Previous months
            if current_date.month - i <= 0:
                year = current_date.year - 1
                month = 12 + (current_date.month - i)
            else:
                year = current_date.year
                month = current_date.month - i
        
        # Calculate start and end of month
        month_start = datetime(year, month, 1).date()
        _, last_day = calendar.monthrange(year, month)
        month_end = datetime(year, month, last_day).date()
        
        # Query flights for this month
        # Use exact calculation for accuracy (same as dashboard)
        month_flights = Flight.objects.filter(
            pilot=user,
            date__gte=month_start,
            date__lte=month_end
        )
        month_hours = sum(flight.exact_flight_minutes for flight in month_flights) / 60
        
        monthly_hours.append({
            'month': month_start.strftime('%b %Y'),
            'hours': float(month_hours)
        })
    
    monthly_hours.reverse()
    
    # Aircraft usage using accurate calculation
    aircraft_usage = calculate_aircraft_usage_accurate(Flight.objects.filter(pilot=user), limit=5)
    
    context = {
        'pilot_profile': pilot_profile,
        'recent_flights': recent_flights,
        'total_flights': total_flights,
        'total_hours': total_hours,
        'total_night_hours': total_night_hours,
        'total_cross_country_hours': total_cross_country_hours,
        'total_instrument_hours': total_instrument_hours,
        'total_dual_hours': total_dual_hours,
        'total_solo_hours': total_solo_hours,
        'total_pic_hours': total_pic_hours,
        'total_day_landings': total_day_landings,
        'total_night_landings': total_night_landings,
        'total_ifr_approaches': total_ifr_approaches,
        'monthly_hours': json.dumps(monthly_hours),
        'aircraft_usage': [
            {
                'registration': item['registration'],
                'manufacturer': item['manufacturer'],
                'type': item['type'],
                'total_hours': item['total_hours'],
                'flight_count': item['flight_count']
            }
            for item in aircraft_usage
        ],
        'avg_flight_time': avg_flight_time,
        'most_used_aircraft': most_used_aircraft,
    }
    
    return render(request, 'logbook/dashboard.html', context)


class FlightListView(LoginRequiredMixin, ListView):
    """List view for flights with search functionality"""
    model = Flight
    template_name = 'logbook/flight_list.html'
    context_object_name = 'flights'
    paginate_by = 10  # Default pagination
    
    def get_paginate_by(self, queryset):
        """Get pagination size from request parameters"""
        try:
            page_size = int(self.request.GET.get('page_size', 10))
            # Ensure page_size is valid
            if page_size <= 0:
                page_size = 10
            return page_size
        except (ValueError, TypeError):
            return 10
    
    def get_queryset(self):
        queryset = Flight.objects.filter(pilot=self.request.user)
        
        # Apply search filters
        form = FlightSearchForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(date__lte=form.cleaned_data['date_to'])
            if form.cleaned_data.get('aircraft'):
                queryset = queryset.filter(aircraft=form.cleaned_data['aircraft'])


        
        return queryset.order_by('-date', '-departure_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = FlightSearchForm(self.request.GET, user=self.request.user)
        
        # Get the filtered queryset (same as get_queryset)
        filtered_queryset = self.get_queryset()
        
        # Calculate statistics for the filtered flights
        context['total_flights'] = filtered_queryset.count()
        # Use exact calculation for accuracy (same as dashboard)
        context['total_hours'] = sum(flight.exact_flight_minutes for flight in filtered_queryset) / 60
        # Convert minutes to hours for display
        total_night_minutes = filtered_queryset.aggregate(total=Sum('night_time'))['total'] or 0
        total_pic_minutes = filtered_queryset.aggregate(total=Sum('pic_time'))['total'] or 0
        context['total_night_hours'] = total_night_minutes / 60
        context['total_pic_hours'] = total_pic_minutes / 60
        

        
        return context


class FlightDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detail view for individual flights"""
    model = Flight
    template_name = 'logbook/flight_detail.html'
    context_object_name = 'flight'
    
    def test_func(self):
        flight = self.get_object()
        return flight.pilot == self.request.user


class FlightCreateView(LoginRequiredMixin, CreateView):
    """Create view for new flights"""
    model = Flight
    form_class = FlightForm
    template_name = 'logbook/flight_form.html'
    
    def get_form_kwargs(self):
        """Ensure form preserves submitted data on validation errors"""
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            # For POST requests, ensure we're using the submitted data
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs
    
    def form_valid(self, form):
        form.instance.pilot = self.request.user
        messages.success(self.request, 'Flight logged successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors - stay on the same page"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect to the newly created flight's detail page"""
        return reverse('flight-detail', kwargs={'pk': self.object.pk})


class FlightUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update view for editing flights"""
    model = Flight
    form_class = FlightForm
    template_name = 'logbook/flight_form.html'
    
    def test_func(self):
        flight = self.get_object()
        return flight.pilot == self.request.user
    
    def get_form_kwargs(self):
        """Ensure form preserves submitted data on validation errors"""
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            # For POST requests, ensure we're using the submitted data
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Flight updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors - stay on the same page"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect to the updated flight's detail page"""
        return reverse('flight-detail', kwargs={'pk': self.object.pk})


class FlightDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete view for flights"""
    model = Flight
    template_name = 'logbook/flight_confirm_delete.html'
    success_url = reverse_lazy('flight-list')
    
    def test_func(self):
        flight = self.get_object()
        return flight.pilot == self.request.user
    
    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion"""
        success_message = 'Flight deleted successfully.'
        
        # Delete the flight first
        self.object = self.get_object()
        self.object.delete()
        
        # Add the success message to Django messages (will persist across redirect)
        messages.success(request, success_message)
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_message,
                'redirect_url': self.get_success_url()
            })
        
        # Regular form submission - redirect with message
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        """Return the URL to redirect to after successful deletion"""
        return reverse('flight-list')


class AircraftListView(LoginRequiredMixin, ListView):
    """List view for aircraft"""
    model = Aircraft
    template_name = 'logbook/aircraft_list.html'
    context_object_name = 'aircraft'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics for the current user's flights
        user_flights = Flight.objects.filter(pilot=self.request.user)
        total_flights = user_flights.count()
        # Use exact calculation for accuracy (same as dashboard)
        total_hours = sum(flight.exact_flight_minutes for flight in user_flights) / 60
        
        # Calculate average hours per aircraft
        aircraft_count = Aircraft.objects.count()
        avg_hours = total_hours / aircraft_count if aircraft_count > 0 else 0
        
        context['total_flights'] = total_flights
        context['total_hours'] = total_hours
        context['avg_hours'] = avg_hours
        
        return context


class AircraftCreateView(LoginRequiredMixin, CreateView):
    """Create view for new aircraft"""
    model = Aircraft
    form_class = AircraftForm
    template_name = 'logbook/aircraft_form.html'
    success_url = reverse_lazy('aircraft-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Aircraft added successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        return super().form_invalid(form)


class AircraftUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for editing aircraft"""
    model = Aircraft
    form_class = AircraftForm
    template_name = 'logbook/aircraft_form.html'
    success_url = reverse_lazy('aircraft-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Aircraft updated successfully!')
        return super().form_valid(form)


class AircraftDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for aircraft"""
    model = Aircraft
    template_name = 'logbook/aircraft_confirm_delete.html'
    success_url = reverse_lazy('aircraft-list')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion"""
        # Get the aircraft before deletion
        aircraft = self.get_object()
        
        # Update all flights associated with this aircraft to preserve all aircraft details
        from .models import Flight
        flights_to_update = Flight.objects.filter(aircraft=aircraft)
        
        for flight in flights_to_update:
            flight.aircraft_registration = aircraft.registration
            flight.aircraft_manufacturer = aircraft.manufacturer
            flight.aircraft_type = aircraft.type
            flight.aircraft_engine_type = aircraft.engine_type
            flight.aircraft = None
            flight.save()
        
        success_message = 'Aircraft deleted successfully.'
        
        # Delete the aircraft first
        self.object = self.get_object()
        self.object.delete()
        
        # Add the success message to Django messages (will persist across redirect)
        messages.success(request, success_message)
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_message,
                'redirect_url': self.get_success_url()
            })
        
        # Regular form submission - redirect with message
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        """Return the URL to redirect to after successful deletion"""
        return reverse('aircraft-list')


@login_required
def profile_view(request):
    """View for pilot profile"""
    pilot_profile, created = PilotProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PilotProfileForm(request.POST, request.FILES, instance=pilot_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = PilotProfileForm(instance=pilot_profile)
    
    context = {
        'form': form,
        'pilot_profile': pilot_profile,
    }
    return render(request, 'logbook/profile.html', context)


@login_required
def charts_view(request):
    """View for flight charts and analytics"""
    user = request.user
    
    # Get pilot profile
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    # Monthly flight hours for the last 12 months
    monthly_data = []
    
    # Get current date
    current_date = timezone.now().date()
    
    for i in range(12):
        # Calculate the month we're looking at
        if i == 0:
            # Current month
            year = current_date.year
            month = current_date.month
        else:
            # Previous months
            if current_date.month - i <= 0:
                year = current_date.year - 1
                month = 12 + (current_date.month - i)
            else:
                year = current_date.year
                month = current_date.month - i
        
        # Calculate start and end of month
        month_start = datetime(year, month, 1).date()
        _, last_day = calendar.monthrange(year, month)
        month_end = datetime(year, month, last_day).date()
        
        month_flights = Flight.objects.filter(
            pilot=user,
            date__gte=month_start,
            date__lte=month_end
        )
        
        # Use exact calculation for accuracy (same as dashboard)
        total_hours = sum(flight.exact_flight_minutes for flight in month_flights) / 60
        night_minutes = month_flights.aggregate(total=Sum('night_time'))['total'] or 0
        # Calculate cross-country hours using new logic (different departure/arrival aerodromes)
        cross_country_minutes = 0
        for flight in month_flights:
            if flight.is_cross_country:
                cross_country_minutes += flight.exact_flight_minutes
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'total_hours': float(total_hours),
            'night_hours': float(night_minutes / 60),
            'cross_country_hours': float(cross_country_minutes / 60),
        })
    
    monthly_data.reverse()
    
    # Aircraft usage using accurate calculation
    aircraft_usage_accurate = calculate_aircraft_usage_accurate(Flight.objects.filter(pilot=user))
    
    # Convert to format expected by charts
    aircraft_data = [
        {
            'aircraft__registration': item['registration'],
            'aircraft__manufacturer': item['manufacturer'] or '',
            'aircraft__type': item['type'] or '',
            'total_hours': float(item['total_hours']),
            'flight_count': item['flight_count']
        }
        for item in aircraft_usage_accurate
    ]
    
    # Engine type distribution
    engine_type_data = Flight.objects.filter(pilot=user).values('aircraft_engine_type').annotate(
        count=Count('id')
    )
    
    # Flight type distribution (based on cross-country and IFR time)
    flight_type_data = []
    
    # Count flights by type using new cross-country logic
    user_flights = Flight.objects.filter(pilot=user)
    cross_country_flights = sum(1 for flight in user_flights if flight.is_cross_country)
    ifr_flights = Flight.objects.filter(pilot=user, ifr_time__gt=0).count()
    night_flights = Flight.objects.filter(pilot=user, night_time__gt=0).count()
    local_flights = sum(1 for flight in user_flights if not flight.is_cross_country and flight.ifr_time == 0 and flight.night_time == 0)
    
    if cross_country_flights > 0:
        flight_type_data.append({'flight_type': 'Cross-Country', 'count': cross_country_flights})
    if ifr_flights > 0:
        flight_type_data.append({'flight_type': 'IFR', 'count': ifr_flights})
    if night_flights > 0:
        flight_type_data.append({'flight_type': 'Night', 'count': night_flights})
    if local_flights > 0:
        flight_type_data.append({'flight_type': 'Local', 'count': local_flights})
    
    
    # Calculate additional statistics
    user_flights = Flight.objects.filter(pilot=user)
    total_flights = user_flights.count()
    # Use exact calculation for accuracy (same as dashboard)
    total_hours = sum(flight.exact_flight_minutes for flight in user_flights) / 60
    avg_flight_time = total_hours / total_flights if total_flights > 0 else 0
    
    
    # Time breakdown data for the radar chart
    # Calculate cross-country hours using new logic
    cross_country_minutes = sum(flight.exact_flight_minutes for flight in user_flights if flight.is_cross_country)
    
    time_breakdown_data = {
        'total_hours': float(total_hours),
        'night_hours': float(user_flights.aggregate(total=Sum('night_time'))['total'] or 0) / 60,
        'ifr_hours': float(user_flights.aggregate(total=Sum('ifr_time'))['total'] or 0) / 60,
        'cross_country_hours': float(cross_country_minutes) / 60,
        'dual_instruction_hours': float(user_flights.aggregate(total=Sum('instructor_time'))['total'] or 0) / 60,
        'solo_hours': float(user_flights.aggregate(total=Sum('pic_time'))['total'] or 0) / 60
    }
    
    # Get most used aircraft
    most_used_aircraft = user_flights.annotate(
        registration=Case(
            When(aircraft__isnull=False, then='aircraft__registration'),
            When(aircraft__isnull=True, aircraft_registration__isnull=True, then=Value('SIM')),
            When(aircraft__isnull=True, aircraft_registration='', then=Value('SIM')),
            default='aircraft_registration',
            output_field=CharField(),
        )
    ).values('registration').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    # Get detailed flight data for CSV export
    flights_data = Flight.objects.filter(pilot=user).select_related('aircraft').order_by('date', 'departure_time')
    flights_for_csv = []
    
    for flight in flights_data:
        flights_for_csv.append({
            'date': flight.date.strftime('%Y-%m-%d'),
            'aircraft': {
                'registration': flight.aircraft.registration if flight.aircraft else flight.aircraft_registration,
                'manufacturer': flight.aircraft.manufacturer if flight.aircraft else flight.aircraft_manufacturer,
                'type': flight.aircraft.type if flight.aircraft else flight.aircraft_type
            },
            'departure_aerodrome': flight.departure_aerodrome,
            'arrival_aerodrome': flight.arrival_aerodrome,
            'total_time': float(flight.total_time or 0),
            'single_engine_time': float(flight.single_engine_time or 0),
            'multi_engine_time': float(flight.multi_engine_time or 0),
            'night_time': float(flight.night_time or 0),
            'ifr_time': float(flight.ifr_time or 0),
            'conditions': 'PIC' if flight.pic_time > 0 else 'Co-Pilot' if flight.copilot_time > 0 else 'Instructor' if flight.instructor_time > 0 else 'Multi-Pilot' if flight.multi_pilot_time > 0 else 'Simulator' if flight.simulator_time > 0 else 'Standard',
            'day_landings': int(flight.day_landings or 0),
            'night_landings': int(flight.night_landings or 0),
            'ifr_approaches': int(flight.ifr_approaches or 0),
            'remarks': flight.remarks
        })
    
    # Flight conditions distribution based on all time fields
    conditions_data = []
    
    # Calculate hours by flight conditions (convert from minutes to hours)
    pic_minutes = Flight.objects.filter(pilot=user, pic_time__gt=0).aggregate(total=Sum('pic_time'))['total'] or 0
    copilot_minutes = Flight.objects.filter(pilot=user, copilot_time__gt=0).aggregate(total=Sum('copilot_time'))['total'] or 0
    instructor_minutes = Flight.objects.filter(pilot=user, instructor_time__gt=0).aggregate(total=Sum('instructor_time'))['total'] or 0
    multi_pilot_minutes = Flight.objects.filter(pilot=user, multi_pilot_time__gt=0).aggregate(total=Sum('multi_pilot_time'))['total'] or 0
    night_minutes = Flight.objects.filter(pilot=user, night_time__gt=0).aggregate(total=Sum('night_time'))['total'] or 0
    ifr_minutes = Flight.objects.filter(pilot=user, ifr_time__gt=0).aggregate(total=Sum('ifr_time'))['total'] or 0
    single_engine_minutes = Flight.objects.filter(pilot=user, single_engine_time__gt=0).aggregate(total=Sum('single_engine_time'))['total'] or 0
    multi_engine_minutes = Flight.objects.filter(pilot=user, multi_engine_time__gt=0).aggregate(total=Sum('multi_engine_time'))['total'] or 0
    simulator_minutes = Flight.objects.filter(pilot=user, simulator_time__gt=0).aggregate(total=Sum('simulator_time'))['total'] or 0
    
    # Calculate cross-country hours using new logic (different departure/arrival aerodromes)
    cross_country_minutes = 0
    for flight in user_flights:
        if flight.is_cross_country:
            cross_country_minutes += flight.exact_flight_minutes
    
    # Add all flight conditions that have time > 0
    if pic_minutes > 0:
        conditions_data.append({'conditions': 'PIC', 'hours': float(pic_minutes) / 60})
    if copilot_minutes > 0:
        conditions_data.append({'conditions': 'SIC', 'hours': float(copilot_minutes) / 60})
    if instructor_minutes > 0:
        conditions_data.append({'conditions': 'DUAL', 'hours': float(instructor_minutes) / 60})
    if multi_pilot_minutes > 0:
        conditions_data.append({'conditions': 'MULTI', 'hours': float(multi_pilot_minutes) / 60})
    if night_minutes > 0:
        conditions_data.append({'conditions': 'NIGHT', 'hours': float(night_minutes) / 60})
    if ifr_minutes > 0:
        conditions_data.append({'conditions': 'IFR', 'hours': float(ifr_minutes) / 60})
    if single_engine_minutes > 0:
        conditions_data.append({'conditions': 'SINGLE ENGINE', 'hours': float(single_engine_minutes) / 60})
    if multi_engine_minutes > 0:
        conditions_data.append({'conditions': 'MULTI ENGINE', 'hours': float(multi_engine_minutes) / 60})
    if simulator_minutes > 0:
        conditions_data.append({'conditions': 'SIMULATOR', 'hours': float(simulator_minutes) / 60})
    if cross_country_minutes > 0:
        conditions_data.append({'conditions': 'CROSS COUNTRY', 'hours': float(cross_country_minutes) / 60})
    
    context = {
        'user': user,
        'pilot_profile': pilot_profile,
        'monthly_data': json.dumps(monthly_data),
        'aircraft_data': json.dumps(aircraft_data),
        'engine_type_data': json.dumps(list(engine_type_data)),
        'flight_type_data': json.dumps(flight_type_data),
        'conditions_data': json.dumps(conditions_data),
        'time_breakdown_data': time_breakdown_data,
        'flights_data': json.dumps(flights_for_csv),
        'total_flights': total_flights,
        'total_hours': float(total_hours),
        'avg_flight_time': float(avg_flight_time),
        'most_used_aircraft': most_used_aircraft['registration'] if most_used_aircraft else 'N/A',
    }
    
    return render(request, 'logbook/charts.html', context)


@login_required
def print_charts_view(request):
    """Print-friendly view for flight charts and analytics"""
    user = request.user
    
    # Get pilot profile
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    # Monthly flight hours for the last 12 months
    monthly_data = []
    
    # Get current date
    current_date = timezone.now().date()
    
    for i in range(12):
        # Calculate the month we're looking at
        if i == 0:
            # Current month
            year = current_date.year
            month = current_date.month
        else:
            # Previous months
            if current_date.month - i <= 0:
                year = current_date.year - 1
                month = 12 + (current_date.month - i)
            else:
                year = current_date.year
                month = current_date.month - i
        
        # Calculate start and end of month
        month_start = datetime(year, month, 1).date()
        _, last_day = calendar.monthrange(year, month)
        month_end = datetime(year, month, last_day).date()
        
        month_flights = Flight.objects.filter(
            pilot=user,
            date__gte=month_start,
            date__lte=month_end
        )
        
        # Use exact calculation for accuracy (same as dashboard)
        total_hours = sum(flight.exact_flight_minutes for flight in month_flights) / 60
        night_minutes = month_flights.aggregate(total=Sum('night_time'))['total'] or 0
        # Calculate cross-country hours using new logic (different departure/arrival aerodromes)
        cross_country_minutes = 0
        for flight in month_flights:
            if flight.is_cross_country:
                cross_country_minutes += flight.exact_flight_minutes
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'total_hours': float(total_hours),
            'night_hours': float(night_minutes / 60),
            'cross_country_hours': float(cross_country_minutes / 60),
        })
    
    monthly_data.reverse()
    
    # Aircraft usage using accurate calculation
    aircraft_usage_accurate = calculate_aircraft_usage_accurate(Flight.objects.filter(pilot=user))
    
    # Convert to format expected by charts
    aircraft_data = [
        {
            'aircraft__registration': item['registration'],
            'aircraft__manufacturer': item['manufacturer'] or '',
            'aircraft__type': item['type'] or '',
            'total_hours': float(item['total_hours']),
            'flight_count': item['flight_count']
        }
        for item in aircraft_usage_accurate
    ]
    
    # Engine type distribution
    engine_type_data = Flight.objects.filter(pilot=user).values('aircraft_engine_type').annotate(
        count=Count('id')
    )
    
    # Flight type distribution (based on cross-country and IFR time)
    flight_type_data = []
    
    # Count flights by type using new cross-country logic
    user_flights = Flight.objects.filter(pilot=user)
    cross_country_flights = sum(1 for flight in user_flights if flight.is_cross_country)
    ifr_flights = Flight.objects.filter(pilot=user, ifr_time__gt=0).count()
    night_flights = Flight.objects.filter(pilot=user, night_time__gt=0).count()
    local_flights = sum(1 for flight in user_flights if not flight.is_cross_country and flight.ifr_time == 0 and flight.night_time == 0)
    
    if cross_country_flights > 0:
        flight_type_data.append({'flight_type': 'Cross-Country', 'count': cross_country_flights})
    if ifr_flights > 0:
        flight_type_data.append({'flight_type': 'IFR', 'count': ifr_flights})
    if night_flights > 0:
        flight_type_data.append({'flight_type': 'Night', 'count': night_flights})
    if local_flights > 0:
        flight_type_data.append({'flight_type': 'Local', 'count': local_flights})
    
    # Calculate additional statistics
    user_flights = Flight.objects.filter(pilot=user)
    total_flights = user_flights.count()
    # Use exact calculation for accuracy (same as dashboard)
    total_hours = sum(flight.exact_flight_minutes for flight in user_flights) / 60
    avg_flight_time = total_hours / total_flights if total_flights > 0 else 0
    
    # Flight conditions distribution based on all time fields
    conditions_data = []
    
    # Calculate hours by flight conditions (convert from minutes to hours)
    pic_minutes = Flight.objects.filter(pilot=user, pic_time__gt=0).aggregate(total=Sum('pic_time'))['total'] or 0
    copilot_minutes = Flight.objects.filter(pilot=user, copilot_time__gt=0).aggregate(total=Sum('copilot_time'))['total'] or 0
    instructor_minutes = Flight.objects.filter(pilot=user, instructor_time__gt=0).aggregate(total=Sum('instructor_time'))['total'] or 0
    multi_pilot_minutes = Flight.objects.filter(pilot=user, multi_pilot_time__gt=0).aggregate(total=Sum('multi_pilot_time'))['total'] or 0
    night_minutes = Flight.objects.filter(pilot=user, night_time__gt=0).aggregate(total=Sum('night_time'))['total'] or 0
    ifr_minutes = Flight.objects.filter(pilot=user, ifr_time__gt=0).aggregate(total=Sum('ifr_time'))['total'] or 0
    single_engine_minutes = Flight.objects.filter(pilot=user, single_engine_time__gt=0).aggregate(total=Sum('single_engine_time'))['total'] or 0
    multi_engine_minutes = Flight.objects.filter(pilot=user, multi_engine_time__gt=0).aggregate(total=Sum('multi_engine_time'))['total'] or 0
    simulator_minutes = Flight.objects.filter(pilot=user, simulator_time__gt=0).aggregate(total=Sum('simulator_time'))['total'] or 0
    
    # Calculate cross-country hours using new logic (different departure/arrival aerodromes)
    cross_country_minutes = 0
    for flight in user_flights:
        if flight.is_cross_country:
            cross_country_minutes += flight.exact_flight_minutes
    
    # Add all flight conditions that have time > 0
    if pic_minutes > 0:
        conditions_data.append({'conditions': 'PIC', 'hours': float(pic_minutes) / 60})
    if copilot_minutes > 0:
        conditions_data.append({'conditions': 'SIC', 'hours': float(copilot_minutes) / 60})
    if instructor_minutes > 0:
        conditions_data.append({'conditions': 'DUAL', 'hours': float(instructor_minutes) / 60})
    if multi_pilot_minutes > 0:
        conditions_data.append({'conditions': 'MULTI', 'hours': float(multi_pilot_minutes) / 60})
    if night_minutes > 0:
        conditions_data.append({'conditions': 'NIGHT', 'hours': float(night_minutes) / 60})
    if ifr_minutes > 0:
        conditions_data.append({'conditions': 'IFR', 'hours': float(ifr_minutes) / 60})
    if single_engine_minutes > 0:
        conditions_data.append({'conditions': 'SINGLE ENGINE', 'hours': float(single_engine_minutes) / 60})
    if multi_engine_minutes > 0:
        conditions_data.append({'conditions': 'MULTI ENGINE', 'hours': float(multi_engine_minutes) / 60})
    if simulator_minutes > 0:
        conditions_data.append({'conditions': 'SIMULATOR', 'hours': float(simulator_minutes) / 60})
    if cross_country_minutes > 0:
        conditions_data.append({'conditions': 'CROSS COUNTRY', 'hours': float(cross_country_minutes) / 60})
    
    # Get most used aircraft
    most_used_aircraft = user_flights.annotate(
        registration=Case(
            When(aircraft__isnull=False, then='aircraft__registration'),
            When(aircraft__isnull=True, aircraft_registration__isnull=True, then=Value('SIM')),
            When(aircraft__isnull=True, aircraft_registration='', then=Value('SIM')),
            default='aircraft_registration',
            output_field=CharField(),
        )
    ).values('registration').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    context = {
        'pilot_profile': pilot_profile,
        'monthly_data': json.dumps(monthly_data),
        'aircraft_data': json.dumps(aircraft_data),
        'engine_type_data': json.dumps(list(engine_type_data)),
        'flight_type_data': json.dumps(flight_type_data),
        'conditions_data': json.dumps(conditions_data),
        'total_flights': total_flights,
        'total_hours': float(total_hours),
        'avg_flight_time': float(avg_flight_time),
        'most_used_aircraft': most_used_aircraft['registration'] if most_used_aircraft else 'N/A',
    }
    
    return render(request, 'logbook/print_charts.html', context)


@login_required
def export_pdf(request):
    """Export flight logbook to PDF with improved formatting and accuracy"""
    user = request.user
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    # Get all flights
    flights = Flight.objects.filter(pilot=user).order_by('date', 'departure_time')
    
    # Calculate accurate totals using exact minutes
    total_flights = flights.count()
    total_hours_minutes = sum(flight.exact_flight_minutes for flight in flights)
    total_pic_time = sum(flight.pic_time for flight in flights)
    total_night_time = sum(flight.night_time for flight in flights)
    total_ifr_time = sum(flight.ifr_time for flight in flights)
    total_landings = sum(flight.day_landings + flight.night_landings for flight in flights)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="flight_logbook_{user.username}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, 
                          leftMargin=0.5*inch, rightMargin=0.5*inch,
                          topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Helper function to convert minutes to hh:mm format
    def minutes_to_hhmm(minutes):
        """Convert minutes to hh:mm format"""
        if not minutes:
            return "00:00"
        h = minutes // 60
        m = minutes % 60
        return f"{int(h):02d}:{int(m):02d}"
    
    # Helper function to convert decimal hours to hh:mm format
    def hours_to_hhmm(hours):
        """Convert decimal hours to hh:mm format"""
        if not hours:
            return "00:00"
        total_minutes = int(hours * 60)
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}"
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold',
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold',
        textColor=colors.darkblue
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        textColor=colors.darkblue
    )
    
    # Title page
    title = Paragraph(f"FLIGHT LOGBOOK", title_style)
    elements.append(title)
    
    subtitle = Paragraph(f"Pilot: {user.get_full_name() or user.username}", subtitle_style)
    elements.append(subtitle)
    
    # Add compliance statement
    compliance_text = "This logbook format is designed to be compatible with both EASA (European Aviation Safety Agency) and FAA (Federal Aviation Administration) requirements."
    compliance_para = Paragraph(compliance_text, styles['Normal'])
    elements.append(compliance_para)
    elements.append(Spacer(1, 30))
    
    # Pilot information section
    pilot_header = Paragraph("PILOT INFORMATION", header_style)
    elements.append(pilot_header)
    
    pilot_info = [
        ['Pilot Name:', user.get_full_name() or user.username],
        ['License Type:', pilot_profile.license_type or 'N/A'],
        ['License Number:', pilot_profile.license_number or 'N/A'],
        ['Medical Class:', pilot_profile.medical_class or 'N/A'],
        ['Medical Expiry:', pilot_profile.medical_expiry.strftime('%d/%m/%Y') if pilot_profile.medical_expiry else 'N/A'],
        ['Flight School:', pilot_profile.flight_school or 'N/A'],
        ['Instructor:', pilot_profile.instructor or 'N/A'],
    ]
    
    pilot_table = Table(pilot_info, colWidths=[2.2*inch, 3.5*inch])
    pilot_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.lightblue, colors.white])
    ]))
    elements.append(pilot_table)
    elements.append(Spacer(1, 20))
    
    # Flight summary section
    summary_header = Paragraph("FLIGHT SUMMARY", header_style)
    elements.append(summary_header)
    
    summary_data = [
        ['Total Flights:', str(total_flights)],
        ['Total Flight Time:', minutes_to_hhmm(total_hours_minutes)],
        ['Total PIC Time:', minutes_to_hhmm(total_pic_time)],
        ['Total Night Time:', minutes_to_hhmm(total_night_time)],
        ['Total IFR Time:', minutes_to_hhmm(total_ifr_time)],
        ['Total Landings:', str(total_landings)],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.2*inch, 3.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.lightgreen, colors.white])
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Flight entries section
    flights_header = Paragraph("FLIGHT ENTRIES", header_style)
    elements.append(flights_header)
    
    # Flight entries table - EASA/FAA compliant format
    flight_headers = ['Date', 'Aircraft', 'Type', 'From', 'To', 'Total', 'Night', 'IFR', 'Role', 'Engine', 'Landings']
    flight_data = [flight_headers]
    
    for flight in flights:
        # Create aircraft type string with manufacturer
        if flight.aircraft:
            aircraft_type = flight.aircraft.type
            if flight.aircraft.manufacturer:
                aircraft_type = f"{flight.aircraft.manufacturer} {flight.aircraft.type}"
            aircraft_registration = flight.aircraft.registration
        else:
            aircraft_type = flight.aircraft_type
            if flight.aircraft_manufacturer:
                aircraft_type = f"{flight.aircraft_manufacturer} {flight.aircraft_type}"
            aircraft_registration = flight.aircraft_registration
        
        # Determine pilot role
        if flight.pic_time > 0:
            role = 'PIC'
        elif flight.copilot_time > 0:
            role = 'SIC'
        elif flight.instructor_time > 0:
            role = 'Dual'
        else:
            role = 'Std'
        
        # Determine engine type
        engine_type = 'SE' if flight.single_engine_time > 0 else 'ME' if flight.multi_engine_time > 0 else 'N/A'
        
        flight_data.append([
            flight.date.strftime('%d/%m/%Y'),  # Use dd/mm/yyyy format
            aircraft_registration or 'N/A',
            aircraft_type[:25] if aircraft_type else 'N/A',  # Increased length
            flight.departure_aerodrome[:15],  # Increased length
            flight.arrival_aerodrome[:15],    # Increased length
            minutes_to_hhmm(flight.exact_flight_minutes),  # Use exact minutes for accuracy
            minutes_to_hhmm(flight.night_time) if flight.night_time > 0 else '00:00',
            minutes_to_hhmm(flight.ifr_time) if flight.ifr_time > 0 else '00:00',
            role,
            engine_type,
            str(flight.day_landings + flight.night_landings),
        ])
    
    # Add totals row
    totals_row = ['TOTALS', '', '', '', '', 
                  minutes_to_hhmm(total_hours_minutes),
                  minutes_to_hhmm(total_night_time),
                  minutes_to_hhmm(total_ifr_time),
                  '', '', str(total_landings)]
    flight_data.append(totals_row)
    
    # Calculate column widths to fit within A4 page width (8.27 inches)
    # Total available width: 8.27 inches - 1 inch margins = 7.27 inches
    col_widths = [0.6*inch, 0.7*inch, 1.0*inch, 0.7*inch, 0.7*inch, 
                   0.6*inch, 0.6*inch, 0.6*inch, 0.5*inch, 0.5*inch, 0.5*inch]
    
    flight_table = Table(flight_data, colWidths=col_widths)
    flight_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        
        # Data rows styling
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
        ('TOPPADDING', (0, 1), (-1, -2), 4),
        
        # Totals row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.darkgreen),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        
        # Grid and alternating row colors
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(flight_table)
    elements.append(Spacer(1, 30))
    
    # Abbreviations and compliance section
    legend_header = Paragraph("ABBREVIATIONS & COMPLIANCE NOTES", header_style)
    elements.append(legend_header)
    
    # Legend content
    legend_data = [
        ['Abbreviation', 'Full Meaning', 'Abbreviation', 'Full Meaning'],
        ['PIC', 'Pilot in Command', 'SIC', 'Second in Command'],
        ['Dual', 'Dual Instruction Received', 'Std', 'Standard Flight'],
        ['SE', 'Single Engine Time', 'ME', 'Multi Engine Time'],
        ['IFR', 'Instrument Flight Rules Time', 'N', 'Night Time'],
        ['D', 'Day Time', 'Landings', 'Total Day + Night Landings'],
        ['Type', 'Manufacturer + Aircraft Type', 'SIM', 'Simulator'],
    ]
    
    legend_table = Table(legend_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.0*inch])
    legend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
    ]))
    elements.append(legend_table)
    elements.append(Spacer(1, 20))
    
    # Footer information
    footer_text = f"""
    <b>Generated by:</b> Wingman Flight Logbook<br/>
    <b>Generated on:</b> {timezone.now().strftime('%d/%m/%Y')}<br/>
    <b>Generated at:</b> {timezone.now().strftime('%H:%M:%S')}<br/>
    <b>Format:</b> FAA/EASA Compatible<br/>
    <b>Total Pages:</b> 1
    """
    
    footer_para = Paragraph(footer_text, styles['Normal'])
    elements.append(footer_para)
    
    # Build PDF
    doc.build(elements)
    return response


@login_required
def export_csv(request):
    """Export flight logbook to CSV"""
    import csv
    
    # Helper function to convert decimal hours to hh:mm format
    def hours_to_hhmm(hours):
        """Convert decimal hours to hh:mm format"""
        if not hours:
            return "00:00"
        total_minutes = int(hours * 60)
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}"
    
    # Helper function to convert minutes to hh:mm format
    def minutes_to_hhmm(minutes):
        """Convert minutes to hh:mm format"""
        if not minutes:
            return "00:00"
        h = minutes // 60
        m = minutes % 60
        return f"{int(h):02d}:{int(m):02d}"
    
    user = request.user
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    # Get all flights
    flights = Flight.objects.filter(pilot=user).order_by('date', 'departure_time')
    
    # Calculate totals - convert all times to minutes for accurate calculations
    total_flights = flights.count()
    total_hours_minutes = sum(flight.exact_flight_minutes for flight in flights)  # Use exact minutes for accuracy
    total_landings = sum(flight.day_landings + flight.night_landings for flight in flights)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="flight_logbook_{user.username}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write pilot details header
    writer.writerow(['PILOT DETAILS'])
    writer.writerow(['Full Name', user.get_full_name() or user.username])
    writer.writerow(['License Number', pilot_profile.license_number or 'N/A'])
    writer.writerow(['License Type', pilot_profile.license_type or 'N/A'])
    writer.writerow(['Medical Expiry', pilot_profile.medical_expiry.strftime('%Y-%m-%d') if pilot_profile.medical_expiry else 'N/A'])
    writer.writerow(['Total Flights', total_flights])
    writer.writerow(['Total Hours', minutes_to_hhmm(total_hours_minutes)])  # Use minutes_to_hhmm for accurate display
    writer.writerow(['Total Landings', total_landings])
    writer.writerow([''])  # Empty row for spacing
    
    # Determine which columns to include based on actual data
    columns_to_include = ['Date', 'AircraftRegistration', 'AircraftType', 'From', 'DepartHour', 'To', 'ArriveHour', 'TotalTime']
    
    # Check if user has any of these time types and add columns accordingly
    has_pic_time = any(flight.pic_time > 0 for flight in flights)
    has_copilot_time = any(flight.copilot_time > 0 for flight in flights)
    has_instructor_time = any(flight.instructor_time > 0 for flight in flights)
    has_single_engine_time = any(flight.single_engine_time > 0 for flight in flights)
    has_multi_engine_time = any(flight.multi_engine_time > 0 for flight in flights)
    has_night_time = any(flight.night_time > 0 for flight in flights)
    if has_night_time:
        has_night_landings = any(flight.night_landings > 0 for flight in flights)
    else:
        has_night_landings = False
    has_ifr_time = any(flight.ifr_time > 0 for flight in flights)
    has_simulator_time = any(flight.simulator_time > 0 for flight in flights)
    has_day_landings = any(flight.day_landings > 0 for flight in flights)
    has_ifr_approaches = any(flight.ifr_approaches > 0 for flight in flights)
    
    # Add conditional columns
    if has_pic_time:
        columns_to_include.append('PIC')
    if has_copilot_time:
        columns_to_include.append('SIC')
    if has_instructor_time:
        columns_to_include.append('DualReceived')
    if has_single_engine_time:
        columns_to_include.append('SingleEngine')
    if has_multi_engine_time:
        columns_to_include.append('MultiEngine')
    if has_night_time:
        columns_to_include.append('NightTime')
    if has_ifr_time:
        columns_to_include.append('IFRTime')
    if has_simulator_time:
        columns_to_include.append('SimulatorTime')
    if has_day_landings:
        columns_to_include.append('DayLandings')
    if has_night_landings:
        columns_to_include.append('NightLandings')
    if has_ifr_approaches:
        columns_to_include.append('IFRApproaches')
    
    # Always include remarks and PIC name
    columns_to_include.append('Remarks')
    columns_to_include.append('PIC Name')
    
    # Add only Total Hours column
    columns_to_include.append('Total Hours')
    
    # Write flight data header
    writer.writerow(['FLIGHT DATA'])
    writer.writerow(columns_to_include)
    
    # Write flight data
    for i, flight in enumerate(flights):
        row_data = []
        
        # Calculate accumulating total hours up to this flight - use exact minutes for accuracy
        flights_up_to_now = flights[:i+1]
        running_total_minutes = sum(f.exact_flight_minutes for f in flights_up_to_now)
        
        # Add required fields
        row_data.extend([
            flight.date.strftime('%d/%m/%Y'),
            flight.aircraft.registration if flight.aircraft else flight.aircraft_registration or 'N/A',
            f"{flight.aircraft.manufacturer} {flight.aircraft.type}" if flight.aircraft and flight.aircraft.manufacturer else flight.aircraft.type if flight.aircraft else flight.aircraft_type or 'N/A',
            flight.departure_aerodrome,
            flight.departure_time.strftime('%H:%M'),
            flight.arrival_aerodrome,
            flight.arrival_time.strftime('%H:%M'),
            minutes_to_hhmm(flight.exact_flight_minutes)
        ])
        
        # Add conditional fields
        if has_pic_time:
            row_data.append(minutes_to_hhmm(flight.pic_time) if flight.pic_time else "00:00")
        if has_copilot_time:
            row_data.append(minutes_to_hhmm(flight.copilot_time) if flight.copilot_time else "00:00")
        if has_instructor_time:
            row_data.append(minutes_to_hhmm(flight.instructor_time) if flight.instructor_time else "00:00")
        if has_single_engine_time:
            row_data.append(minutes_to_hhmm(flight.single_engine_time) if flight.single_engine_time else "00:00")
        if has_multi_engine_time:
            row_data.append(minutes_to_hhmm(flight.multi_engine_time) if flight.multi_engine_time else "00:00")
        if has_night_time:
            row_data.append(minutes_to_hhmm(flight.night_time) if flight.night_time else "00:00")
        if has_ifr_time:
            row_data.append(minutes_to_hhmm(flight.ifr_time) if flight.ifr_time else "00:00")
        if has_simulator_time:
            row_data.append(minutes_to_hhmm(flight.simulator_time) if flight.simulator_time else "00:00")
        if has_day_landings:
            row_data.append(flight.day_landings)
        if has_night_landings:
            row_data.append(flight.night_landings)
        if has_ifr_approaches:
            row_data.append(flight.ifr_approaches)
        
        # Always add remarks, PIC name, and total hours
        row_data.append(flight.remarks or '')
        row_data.append(user.get_full_name() or user.username)
        row_data.append(minutes_to_hhmm(running_total_minutes))  # Use minutes_to_hhmm for accurate display
        
        writer.writerow(row_data)
    
    # Add empty row for spacing
    writer.writerow([' '])
    
    # Calculate totals for all columns - use exact minutes for accurate calculations
    total_flights = len(flights)
    total_hours_minutes = sum(flight.exact_flight_minutes for flight in flights)  # Use exact minutes for accuracy
    total_pic_time = sum(flight.pic_time for flight in flights)  # Already in minutes
    total_copilot_time = sum(flight.copilot_time for flight in flights)  # Already in minutes
    total_instructor_time = sum(flight.instructor_time for flight in flights)  # Already in minutes
    total_single_engine_time = sum(flight.single_engine_time for flight in flights)  # Already in minutes
    total_multi_engine_time = sum(flight.multi_engine_time for flight in flights)  # Already in minutes
    total_night_time = sum(flight.night_time for flight in flights)  # Already in minutes
    total_ifr_time = sum(flight.ifr_time for flight in flights)  # Already in minutes
    total_simulator_time = sum(flight.simulator_time for flight in flights)  # Already in minutes
    total_day_landings = sum(flight.day_landings for flight in flights)
    total_night_landings = sum(flight.night_landings for flight in flights)
    total_ifr_approaches = sum(flight.ifr_approaches for flight in flights)
    

    # Create totals row - start with TOTALS label
    totals_row = ['TOTALS']
    
    # Add empty fields for required fields (Date, AircraftRegistration, AircraftType, From, DepartHour, To, ArriveHour, TotalTime)
    # These fields don't have totals, so they remain empty
    totals_row.extend(['', '', '', '', '', ''])
    
    # Add totals for conditional fields in the same order as they appear in flight data
    totals_row.append(minutes_to_hhmm(total_hours_minutes))  # Use minutes_to_hhmm for accurate display
    if has_pic_time:
        totals_row.append(minutes_to_hhmm(total_pic_time))
    if has_copilot_time:
        totals_row.append(minutes_to_hhmm(total_copilot_time))
    if has_instructor_time:
        totals_row.append(minutes_to_hhmm(total_instructor_time))
    if has_single_engine_time:
        totals_row.append(minutes_to_hhmm(total_single_engine_time))
    if has_multi_engine_time:
        totals_row.append(minutes_to_hhmm(total_multi_engine_time))
    if has_night_time:
        totals_row.append(minutes_to_hhmm(total_night_time))
    if has_ifr_time:
        totals_row.append(minutes_to_hhmm(total_ifr_time))
    if has_simulator_time:
        totals_row.append(minutes_to_hhmm(total_simulator_time))
    if has_day_landings:
        totals_row.append(total_day_landings)
    if has_night_landings:
        totals_row.append(total_night_landings)
    if has_ifr_approaches:
        totals_row.append(total_ifr_approaches)
    
    # Add empty fields for remarks and PIC name, then total hours
    totals_row.extend(['', '', minutes_to_hhmm(total_hours_minutes)])  # Use minutes_to_hhmm for accurate display
    
    # Write totals row
    writer.writerow(totals_row)
    
    # Add footer information in separate sections to avoid affecting column widths
    writer.writerow([' '])  # Empty row for spacing
    
    # Footer section 1 - End marker
    writer.writerow(['END OF FLIGHT LOG'])
    
    # Footer section 2 - Generation info (single column to avoid affecting flight data columns)
    writer.writerow([''])
    writer.writerow(['GENERATION INFO'])
    writer.writerow(['Generated by', 'Wingman Flight Logbook'])
    writer.writerow(['Generated on', timezone.now().strftime("%Y-%m-%d")])
    writer.writerow(['Generated at', timezone.now().strftime("%H:%M:%S")])
    
    # Footer section 3 - Compliance notes (single column to avoid affecting flight data columns)
    writer.writerow([''])
    writer.writerow(['COMPLIANCE NOTES'])
    writer.writerow(['Format', 'FAA/EASA Compatible'])
    
    return response


@login_required
def api_flight_stats(request):
    """API endpoint for flight statistics"""
    user = request.user
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    stats = {
        'total_hours': float(pilot_profile.total_flight_hours),
        'total_night_hours': float(pilot_profile.total_night_hours),
        'total_cross_country_hours': float(pilot_profile.total_cross_country_hours),
        'total_instrument_hours': float(pilot_profile.total_instrument_hours),
        'total_dual_hours': float(pilot_profile.total_dual_hours),
        'total_solo_hours': float(pilot_profile.total_solo_hours),
        'total_pic_hours': float(pilot_profile.total_pic_hours),
        'total_flights': Flight.objects.filter(pilot=user).count(),
    }
    
    return JsonResponse(stats)


@ratelimit(key='ip', rate='3/h', method='POST', block=False)
def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        # Check rate limiting and show messages instead of blocking
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            logger.warning(f'Password reset rate limit exceeded from IP: {get_client_ip(request)}')
            messages.error(request, 'Too many password reset attempts. Please wait a few hours before trying again for security reasons.')
            form = PasswordResetRequestForm()
            return render(request, 'logbook/password_reset_request.html', {'form': form})
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)
                # Generate token and send email
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset URL
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                # Send password reset email
                try:
                    # send_mail(
                    #     subject,
                    #     message,
                    #     None,  # Use DEFAULT_FROM_EMAIL
                    #     [email],
                    #     fail_silently=False,
                    # )

                    r = resend.Emails.send({
                    "from": "onboarding@resend.dev",
                    "to": "henkaoua@student.42lausanne.ch",
                    "subject": "Hello World",
                    "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
                    })
                    logger.info(f'Password reset email sent successfully to {email}')
                except Exception as e:
                    logger.error(f'Failed to send password reset email to {email}: {str(e)}')
                    messages.error(request, 'Failed to send password reset email. Please try again later.')
                    return render(request, 'logbook/password_reset_request.html', {'form': form})
                
                messages.success(request, 'Password reset email has been sent. Please check your inbox.')
                return redirect('login')
                
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                pass
            
            messages.success(request, 'If an account with that email exists, a password reset email has been sent.')
            return redirect('login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'logbook/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
                return redirect('login')
        else:
            form = SetPasswordForm()
        
        return render(request, 'logbook/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('login')


def privacy_policy(request):
    """Privacy Policy page"""
    from django.utils import timezone
    context = {
        'last_updated': timezone.now().strftime('%B %d, %Y')
    }
    return render(request, 'privacy_policy.html', context)


def terms_of_service(request):
    """Terms of Service page"""
    from django.utils import timezone
    context = {
        'last_updated': timezone.now().strftime('%B %d, %Y')
    }
    return render(request, 'terms_of_service.html', context)



