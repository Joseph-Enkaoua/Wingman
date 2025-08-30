from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Flight, Aircraft, PilotProfile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML


class FlightForm(forms.ModelForm):
    """Form for creating and editing flight entries"""
    
    class Meta:
        model = Flight
        fields = [
            'date', 'aircraft', 'departure_aerodrome', 'arrival_aerodrome',
            'departure_time', 'arrival_time', 'pilot_role', 'conditions',
            'flight_type', 'night_time', 'instrument_time', 'cross_country_time',
            'instructor_name', 'instructor_rating', 'landings_day', 'landings_night',
            'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'arrival_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'night_time': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'form-control'}),
            'instrument_time': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'form-control'}),
            'cross_country_time': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'form-control'}),
            'landings_day': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'landings_night': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-vertical'
        self.helper.label_class = ''
        self.helper.field_class = ''
        
        # Determine button text based on whether this is an update or create
        button_text = 'Update Flight' if self.instance and self.instance.pk else 'Log Flight'
        
        self.helper.layout = Layout(
            Row(
                Column('date', css_class='form-group col-md-6'),
                Column('aircraft', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('departure_aerodrome', css_class='form-group col-md-6'),
                Column('arrival_aerodrome', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('departure_time', css_class='form-group col-md-6'),
                Column('arrival_time', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('pilot_role', css_class='form-group col-md-4'),
                Column('conditions', css_class='form-group col-md-4'),
                Column('flight_type', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('night_time', css_class='form-group col-md-4'),
                Column('instrument_time', css_class='form-group col-md-4'),
                Column('cross_country_time', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('instructor_name', css_class='form-group col-md-6'),
                Column('instructor_rating', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('landings_day', css_class='form-group col-md-6'),
                Column('landings_night', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            'remarks',
            Row(
                Column(
                    HTML('<div class="d-flex justify-content-between">'),
                    HTML('<a href="{% url \'flight-list\' %}" class="btn btn-outline-secondary"><i class="fas fa-times"></i> Cancel</a>'),
                    Submit('submit', button_text, css_class='btn btn-primary'),
                    HTML('</div>'),
                    css_class='form-group col-md-12'
                ),
                css_class='form-row'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        date = cleaned_data.get('date')
        
        if departure_time and arrival_time and date:
            from datetime import datetime
            from datetime import timedelta
            
            departure_dt = datetime.combine(date, departure_time)
            arrival_dt = datetime.combine(date, arrival_time)
            
            # Handle overnight flights
            if arrival_dt < departure_dt:
                arrival_dt += timedelta(days=1)
            
            # Calculate flight duration
            duration = arrival_dt - departure_dt
            total_hours = duration.total_seconds() / 3600
            
            # Validate flight duration
            if total_hours < 0.1:
                raise forms.ValidationError("Flight duration must be at least 0.1 hours")
            elif total_hours > 24:
                raise forms.ValidationError("Flight duration cannot exceed 24 hours")
            
            # Auto-calculate total time
            cleaned_data['total_time'] = round(total_hours, 1)
        
        return cleaned_data


class AircraftForm(forms.ModelForm):
    """Form for creating and editing aircraft"""
    
    class Meta:
        model = Aircraft
        fields = ['registration', 'type', 'manufacturer', 'year_manufactured', 'total_time']
        widgets = {
            'registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'F-GABC'}),
            'type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cessna 152'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cessna'}),
            'year_manufactured': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2030'}),
            'total_time': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Aircraft', css_class='btn btn-primary'))
    
    def clean_registration(self):
        registration = self.cleaned_data['registration']
        if registration:
            registration = registration.upper().strip()
        return registration


class PilotProfileForm(forms.ModelForm):
    """Form for editing pilot profile"""
    
    class Meta:
        model = PilotProfile
        fields = [
            'license_number', 'license_type', 'medical_class', 'medical_expiry',
            'phone', 'address', 'flight_school', 'instructor', 'profile_picture'
        ]
        widgets = {
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PPL, CPL, ATPL'}),
            'medical_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class 1, Class 2'}),
            'medical_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'flight_school': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Save Profile', css_class='btn btn-primary'))


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Register', css_class='btn btn-primary'))
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create pilot profile
            PilotProfile.objects.create(user=user)
        return user


class FlightSearchForm(forms.Form):
    """Form for searching flights"""
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    aircraft = forms.ModelChoiceField(queryset=Aircraft.objects.all(), required=False, empty_label="All Aircraft")
    pilot_role = forms.ChoiceField(choices=[('', 'All Roles')] + Flight.PILOT_ROLE_CHOICES, required=False)
    conditions = forms.ChoiceField(choices=[('', 'All Conditions')] + Flight.CONDITIONS_CHOICES, required=False)
    flight_type = forms.ChoiceField(choices=[('', 'All Types')] + Flight.FLIGHT_TYPE_CHOICES, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.add_input(Submit('submit', 'Search', css_class='btn btn-primary'))
