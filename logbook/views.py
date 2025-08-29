from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import io
from decimal import Decimal

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Flight, Aircraft, PilotProfile
from .forms import FlightForm, AircraftForm, PilotProfileForm, UserRegistrationForm, FlightSearchForm


def logout_view(request):
    """Simple logout view that clears session and redirects to login"""
    from django.contrib.auth import logout
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
    
    # Monthly flight hours for the last 12 months
    monthly_hours = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        month_hours = Flight.objects.filter(
            pilot=user,
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('total_time'))['total'] or 0
        
        monthly_hours.append({
            'month': month_start.strftime('%b %Y'),
            'hours': float(month_hours)
        })
    
    monthly_hours.reverse()
    
    # Aircraft usage
    aircraft_usage = Flight.objects.filter(pilot=user).values('aircraft__registration').annotate(
        total_hours=Sum('total_time'),
        flight_count=Count('id')
    ).order_by('-total_hours')[:5]
    
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
        'monthly_hours': json.dumps(monthly_hours),
        'aircraft_usage': aircraft_usage,
    }
    
    return render(request, 'logbook/dashboard.html', context)


class FlightListView(LoginRequiredMixin, ListView):
    """List view for flights with search functionality"""
    model = Flight
    template_name = 'logbook/flight_list.html'
    context_object_name = 'flights'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Flight.objects.filter(pilot=self.request.user)
        
        # Apply search filters
        form = FlightSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(date__lte=form.cleaned_data['date_to'])
            if form.cleaned_data.get('aircraft'):
                queryset = queryset.filter(aircraft=form.cleaned_data['aircraft'])
            if form.cleaned_data.get('pilot_role'):
                queryset = queryset.filter(pilot_role=form.cleaned_data['pilot_role'])
            if form.cleaned_data.get('conditions'):
                queryset = queryset.filter(conditions=form.cleaned_data['conditions'])
            if form.cleaned_data.get('flight_type'):
                queryset = queryset.filter(flight_type=form.cleaned_data['flight_type'])
        
        return queryset.order_by('-date', '-departure_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = FlightSearchForm(self.request.GET)
        
        # Calculate statistics for the current user's flights
        user_flights = Flight.objects.filter(pilot=self.request.user)
        context['total_hours'] = user_flights.aggregate(total=Sum('total_time'))['total'] or 0
        context['total_night_hours'] = user_flights.aggregate(total=Sum('night_time'))['total'] or 0
        context['total_cross_country_hours'] = user_flights.aggregate(total=Sum('cross_country_time'))['total'] or 0
        
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
    success_url = reverse_lazy('flight-list')
    
    def form_valid(self, form):
        form.instance.pilot = self.request.user
        messages.success(self.request, 'Flight logged successfully!')
        return super().form_valid(form)


class FlightUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update view for editing flights"""
    model = Flight
    form_class = FlightForm
    template_name = 'logbook/flight_form.html'
    success_url = reverse_lazy('flight-list')
    
    def test_func(self):
        flight = self.get_object()
        return flight.pilot == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Flight updated successfully!')
        return super().form_valid(form)


class FlightDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete view for flights"""
    model = Flight
    template_name = 'logbook/flight_confirm_delete.html'
    success_url = reverse_lazy('flight-list')
    
    def test_func(self):
        flight = self.get_object()
        return flight.pilot == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Flight deleted successfully!')
        return super().delete(request, *args, **kwargs)


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
        total_hours = user_flights.aggregate(total=Sum('total_time'))['total'] or 0
        
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
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Aircraft deleted successfully!')
        return super().delete(request, *args, **kwargs)


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
    
    # Monthly flight hours for the last 12 months
    monthly_data = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        month_flights = Flight.objects.filter(
            pilot=user,
            date__gte=month_start,
            date__lte=month_end
        )
        
        total_hours = month_flights.aggregate(total=Sum('total_time'))['total'] or 0
        night_hours = month_flights.aggregate(total=Sum('night_time'))['total'] or 0
        cross_country_hours = month_flights.aggregate(total=Sum('cross_country_time'))['total'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'total_hours': float(total_hours),
            'night_hours': float(night_hours),
            'cross_country_hours': float(cross_country_hours),
        })
    
    monthly_data.reverse()
    
    # Aircraft usage
    aircraft_data = Flight.objects.filter(pilot=user).values('aircraft__registration').annotate(
        total_hours=Sum('total_time'),
        flight_count=Count('id')
    ).order_by('-total_hours')
    
    # Flight type distribution
    flight_type_data = Flight.objects.filter(pilot=user).values('flight_type').annotate(
        count=Count('id')
    )
    
    # Conditions distribution
    conditions_data = Flight.objects.filter(pilot=user).values('conditions').annotate(
        count=Count('id')
    )
    
    context = {
        'monthly_data': json.dumps(monthly_data),
        'aircraft_data': list(aircraft_data),
        'flight_type_data': list(flight_type_data),
        'conditions_data': list(conditions_data),
    }
    
    return render(request, 'logbook/charts.html', context)


@login_required
def export_pdf(request):
    """Export flight logbook to PDF"""
    user = request.user
    pilot_profile, created = PilotProfile.objects.get_or_create(user=user)
    
    # Get all flights
    flights = Flight.objects.filter(pilot=user).order_by('date', 'departure_time')
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="flight_logbook_{user.username}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Title
    title = Paragraph(f"Flight Logbook - {user.get_full_name()}", title_style)
    elements.append(title)
    
    # Pilot information
    pilot_info = [
        ['Pilot Name:', user.get_full_name()],
        ['License Type:', pilot_profile.license_type or 'N/A'],
        ['License Number:', pilot_profile.license_number or 'N/A'],
        ['Total Flight Hours:', f"{pilot_profile.total_flight_hours:.1f}"],
        ['Total Night Hours:', f"{pilot_profile.total_night_hours:.1f}"],
        ['Total Cross-Country Hours:', f"{pilot_profile.total_cross_country_hours:.1f}"],
    ]
    
    pilot_table = Table(pilot_info, colWidths=[2*inch, 4*inch])
    pilot_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(pilot_table)
    elements.append(Spacer(1, 20))
    
    # Flight entries table
    flight_data = [['Date', 'Aircraft', 'From', 'To', 'Total', 'Night', 'XC', 'Role', 'Conditions']]
    
    for flight in flights:
        flight_data.append([
            flight.date.strftime('%Y-%m-%d'),
            flight.aircraft.registration,
            flight.departure_aerodrome,
            flight.arrival_aerodrome,
            f"{flight.total_time:.1f}",
            f"{flight.night_time:.1f}",
            f"{flight.cross_country_time:.1f}",
            flight.get_pilot_role_display(),
            flight.get_conditions_display(),
        ])
    
    flight_table = Table(flight_data, colWidths=[0.8*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.8*inch, 0.8*inch])
    flight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(flight_table)
    
    # Build PDF
    doc.build(elements)
    return response


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'logbook/register.html', {'form': form})


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
