from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Flight, Aircraft, PilotProfile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password


class TimeToDecimalField(forms.CharField):
    """Custom field that accepts time input (HH:MM) and converts to decimal hours"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': 'HH:MM'
        })
    
    def prepare_value(self, value):
        """Convert decimal hours back to time format for initial value display"""
        if value is not None and value != '':
            try:
                # Convert decimal hours to hours and minutes
                value = float(value)
                hours = int(value)
                minutes = int((value - hours) * 60)
                # Return time string in HH:MM format
                return f"{hours:02d}:{minutes:02d}"
            except (ValueError, TypeError):
                return value
        return value
    
    def clean(self, value):
        """Convert time input to decimal hours"""
        if not value:
            return 0.0
        
        try:
            # Parse HH:MM format
            if ':' in str(value):
                hours, minutes = map(int, str(value).split(':'))
                # Convert to decimal hours
                total_hours = hours + (minutes / 60)
                return round(total_hours, 1)
            else:
                # Try to convert directly to float
                return round(float(value), 1)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please enter time in HH:MM format (e.g., 02:30)")


class FlightForm(forms.ModelForm):
    """Form for creating and editing flight entries"""
    
    # Custom fields for time inputs
    night_time = TimeToDecimalField(required=False, label="Night Time")
    instrument_time = TimeToDecimalField(required=False, label="Instrument Time")
    cross_country_time = TimeToDecimalField(required=False, label="Cross Country Time")
    
    class Meta:
        model = Flight
        fields = [
            'date', 'aircraft', 'departure_aerodrome', 'arrival_aerodrome',
            'departure_time', 'arrival_time', 'pilot_role', 'conditions',
            'flight_type', 'instructor_name', 'instructor_rating', 'landings_day', 'landings_night',
            'remarks', 'night_time', 'instrument_time', 'cross_country_time'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'arrival_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'landings_day': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'landings_night': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        """Override save to handle custom time fields"""
        flight = super().save(commit=False)
        
        # Set the time values from our custom fields
        flight.night_time = self.cleaned_data.get('night_time', 0.0)
        flight.instrument_time = self.cleaned_data.get('instrument_time', 0.0)
        flight.cross_country_time = self.cleaned_data.get('cross_country_time', 0.0)
        
        if commit:
            flight.save()
        return flight
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-vertical'
        self.helper.label_class = ''
        self.helper.field_class = ''
        
        # Determine button text based on whether this is an update or create
        button_text = 'Update Flight' if self.instance and self.instance.pk else 'Log Flight'
        
        # Set initial values for custom time fields when editing
        if self.instance and self.instance.pk:
            # Convert decimal hours to time format for display
            if self.instance.night_time:
                self.fields['night_time'].initial = self._decimal_to_time(self.instance.night_time)
            if self.instance.instrument_time:
                self.fields['instrument_time'].initial = self._decimal_to_time(self.instance.instrument_time)
            if self.instance.cross_country_time:
                self.fields['cross_country_time'].initial = self._decimal_to_time(self.instance.cross_country_time)
        
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
        night_time = cleaned_data.get('night_time')
        instrument_time = cleaned_data.get('instrument_time')
        cross_country_time = cleaned_data.get('cross_country_time')
        
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
            
            # Validate that time components don't exceed total flight time
            if night_time and night_time > total_hours:
                raise forms.ValidationError(f"Night time ({night_time:.1f}h) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if instrument_time and instrument_time > total_hours:
                raise forms.ValidationError(f"Instrument time ({instrument_time:.1f}h) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if cross_country_time and cross_country_time > total_hours:
                raise forms.ValidationError(f"Cross country time ({cross_country_time:.1f}h) cannot exceed total flight time ({total_hours:.1f}h)")
        
        return cleaned_data
    
    def _decimal_to_time(self, decimal_hours):
        """Convert decimal hours to time string format (HH:MM)"""
        if decimal_hours is None or decimal_hours == 0:
            return "00:00"
        
        try:
            hours = int(decimal_hours)
            minutes = int((decimal_hours - hours) * 60)
            return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            return "00:00"


class AircraftForm(forms.ModelForm):
    """Form for creating and editing aircraft"""
    
    class Meta:
        model = Aircraft
        fields = ['registration', 'type', 'manufacturer', 'year_manufactured', 'engine_type', 'total_time']
        widgets = {
            'registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'F-GABC'}),
            'type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cessna 152'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cessna'}),
            'year_manufactured': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2030'}),
            'engine_type': forms.Select(attrs={'class': 'form-control'}),
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
            'phone', 'address', 'flight_school', 'instructor'
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
    
    def clean_email(self):
        """Ensure email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Pilot profile is now created automatically via signals
        return user


class FlightSearchForm(forms.Form):
    """Form for searching flights"""
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    aircraft = forms.ModelChoiceField(queryset=Aircraft.objects.none(), required=False, empty_label="All Aircraft")
    pilot_role = forms.ChoiceField(choices=[('', 'All Roles')] + list(Flight.PILOT_ROLE_CHOICES), required=False)
    conditions = forms.ChoiceField(choices=[('', 'All Conditions')] + list(Flight.CONDITIONS_CHOICES), required=False)
    flight_type = forms.ChoiceField(choices=[('', 'All Types')] + list(Flight.FLIGHT_TYPE_CHOICES), required=False)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['aircraft'].queryset = Aircraft.objects.all()


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset"""
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError(
                "No active account found with this email address."
            )
        return email


class SetPasswordForm(forms.Form):
    """Form for setting new password"""
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        }),
    )
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
        validate_password(password2)
        return password2
