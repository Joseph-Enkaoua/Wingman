from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Flight, Aircraft, PilotProfile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password


class TimeInMinutesField(forms.TimeField):
    """Custom field that accepts time input (HH:MM) and converts to minutes for storage"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'HH:00'
        })
    
    def prepare_value(self, value):
        """Convert minutes back to time format for initial value display"""
        print(f"DEBUG: prepare_value called with value: {value} (type: {type(value)})")
        if value is not None and value != '' and value != 0:
            try:
                # Convert minutes to hours and minutes
                value = int(value)
                hours = value // 60
                minutes = value % 60
                # Return time string in HH:MM format
                result = f"{hours:02d}:{minutes:02d}"
                print(f"DEBUG: Converting {value} minutes to {result}")
                return result
            except (ValueError, TypeError) as e:
                print(f"DEBUG: Error converting value: {e}")
                return "00:00"
        print(f"DEBUG: Returning 00:00 for value: {value}")
        return "00:00"
    
    def clean(self, value):
        """Convert time input to minutes"""
        if not value or value == "00:00":
            return 0
        
        try:
            # Parse HH:MM format
            if ':' in str(value):
                hours, minutes = map(int, str(value).split(':'))
                # Convert to total minutes
                total_minutes = hours * 60 + minutes
                return total_minutes
            else:
                # Try to convert directly to integer (assuming minutes)
                return int(value)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please enter time in HH:MM format (e.g., 02:30)")


class FlightForm(forms.ModelForm):
    """Form for creating and editing flight entries"""
    
    # Custom fields for time inputs - new structure (removed single_engine_time and multi_engine_time)
    multi_pilot_time = TimeInMinutesField(required=False, label="Multi-Pilot Flight Time")
    night_time = TimeInMinutesField(required=False, label="Night Flight Time")
    ifr_time = TimeInMinutesField(required=False, label="IFR Flight Time")
    pic_time = TimeInMinutesField(required=False, label="PIC Time")
    copilot_time = TimeInMinutesField(required=False, label="Co-Pilot Time")
    double_command_time = TimeInMinutesField(required=False, label="Double Command Time")
    instructor_time = TimeInMinutesField(required=False, label="Instructor Time")
    simulator_time = TimeInMinutesField(required=False, label="Simulator Time")
    

    

    
    # PIC field
    pic_name = forms.CharField(
        max_length=100,
        required=False,
        label="Pilot in Command (PIC)",
        help_text="Name of the pilot in command",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter PIC name'
        })
    )
    
    class Meta:
        model = Flight
        fields = [
            'date', 'aircraft', 'departure_aerodrome', 'arrival_aerodrome', 'departure_time', 'arrival_time', 'pic_name',
            'multi_pilot_time', 'day_landings', 'night_landings',
            'ifr_approaches', 'night_time', 'ifr_time', 'pic_time', 'copilot_time', 'double_command_time',
            'instructor_time', 'simulator_type', 'simulator_time', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'aircraft': forms.Select(attrs={'class': 'form-control'}),
            'departure_aerodrome': forms.TextInput(attrs={'class': 'form-control'}),
            'arrival_aerodrome': forms.TextInput(attrs={'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'arrival_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'day_landings': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'night_landings': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'ifr_approaches': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'simulator_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FNPT II, FFS'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        """Override save to handle custom time fields and aircraft data"""
        flight = super().save(commit=False)
        
        # Set the time values from our custom fields
        flight.multi_pilot_time = self.cleaned_data.get('multi_pilot_time', 0)
        flight.night_time = self.cleaned_data.get('night_time', 0)
        flight.ifr_time = self.cleaned_data.get('ifr_time', 0)
        flight.pic_time = self.cleaned_data.get('pic_time', 0)
        flight.copilot_time = self.cleaned_data.get('copilot_time', 0)
        flight.double_command_time = self.cleaned_data.get('double_command_time', 0)
        flight.instructor_time = self.cleaned_data.get('instructor_time', 0)
        flight.simulator_time = self.cleaned_data.get('simulator_time', 0)
        
        # Handle aircraft data
        aircraft = self.cleaned_data.get('aircraft')
        
        if aircraft:
            # Aircraft selected from list - populate preserved fields
            flight.aircraft_registration = aircraft.registration
            flight.aircraft_manufacturer = aircraft.manufacturer
            flight.aircraft_type = aircraft.type
            flight.aircraft_engine_type = aircraft.engine_type
            
            # Auto-populate engine time based on aircraft type and flight duration
            if aircraft.engine_type == 'SINGLE':
                flight.single_engine_time = int(flight.total_time * 60) if flight.total_time else 0
                flight.multi_engine_time = 0
            elif aircraft.engine_type == 'MULTI':
                flight.multi_engine_time = int(flight.total_time * 60) if flight.total_time else 0
                flight.single_engine_time = 0
        else:
            # No aircraft selected - this is allowed for simulator flights
            flight.aircraft = None
            flight.aircraft_registration = ''
            flight.aircraft_manufacturer = ''
            flight.aircraft_type = ''
            flight.aircraft_engine_type = ''
            # Set both engine times to 0 for simulator flights
            flight.single_engine_time = 0
            flight.multi_engine_time = 0
        
        if commit:
            flight.save()
        return flight
    
    def clean(self):
        cleaned_data = super().clean()
        aircraft = cleaned_data.get('aircraft')
        
        # Aircraft is now optional - simulator flights don't require aircraft
        # No validation needed for aircraft field
        
        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        date = cleaned_data.get('date')
        multi_pilot_time = cleaned_data.get('multi_pilot_time')
        night_time = cleaned_data.get('night_time')
        ifr_time = cleaned_data.get('ifr_time')
        pic_time = cleaned_data.get('pic_time')
        copilot_time = cleaned_data.get('copilot_time')
        double_command_time = cleaned_data.get('double_command_time')
        instructor_time = cleaned_data.get('instructor_time')
        simulator_time = cleaned_data.get('simulator_time')
        
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
            total_minutes = int(duration.total_seconds() / 60)
            
            # Validate flight duration
            if total_hours < 0.1:
                raise forms.ValidationError("Flight duration must be at least 0.1 hours")
            elif total_hours > 24:
                raise forms.ValidationError("Flight duration cannot exceed 24 hours")
            
            # Auto-calculate total time
            cleaned_data['total_time'] = round(total_hours, 1)
            
            # Validate that time components don't exceed total flight time (convert to minutes for comparison)
            if night_time and night_time > total_minutes:
                night_hours = night_time // 60
                night_mins = night_time % 60
                raise forms.ValidationError(f"Night time ({night_hours:02d}:{night_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if ifr_time and ifr_time > total_minutes:
                ifr_hours = ifr_time // 60
                ifr_mins = ifr_time % 60
                raise forms.ValidationError(f"IFR time ({ifr_hours:02d}:{ifr_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            

            # Validate that role time components don't exceed total flight time
            if pic_time and pic_time > total_minutes:
                pic_hours = pic_time // 60
                pic_mins = pic_time % 60
                raise forms.ValidationError(f"PIC time ({pic_hours:02d}:{pic_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if copilot_time and copilot_time > total_minutes:
                cp_hours = copilot_time // 60
                cp_mins = copilot_time % 60
                raise forms.ValidationError(f"Co-pilot time ({cp_hours:02d}:{cp_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            
            # Validate that other time components don't exceed total flight time
            if multi_pilot_time and multi_pilot_time > total_minutes:
                mp_hours = multi_pilot_time // 60
                mp_mins = multi_pilot_time % 60
                raise forms.ValidationError(f"Multi-pilot time ({mp_hours:02d}:{mp_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if double_command_time and double_command_time > total_minutes:
                dc_hours = double_command_time // 60
                dc_mins = double_command_time % 60
                raise forms.ValidationError(f"Double command time ({dc_hours:02d}:{dc_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if instructor_time and instructor_time > total_minutes:
                inst_hours = instructor_time // 60
                inst_mins = instructor_time % 60
                raise forms.ValidationError(f"Instructor time ({inst_hours:02d}:{inst_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
            
            if simulator_time and simulator_time > total_minutes:
                sim_hours = simulator_time // 60
                sim_mins = simulator_time % 60
                raise forms.ValidationError(f"Simulator time ({sim_hours:02d}:{sim_mins:02d}) cannot exceed total flight time ({total_hours:.1f}h)")
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-vertical'
        self.helper.label_class = ''
        self.helper.field_class = ''
        
        # Update aircraft field to include a "None" option
        self.fields['aircraft'].label = "Select Aircraft"
        self.fields['aircraft'].empty_label = "Choose from list..."
        self.fields['aircraft'].help_text = "Select an aircraft from your registered aircraft (optional for simulator flights)"
        self.fields['aircraft'].required = False
        

        

        
        # Determine button text based on whether this is an update or create
        button_text = 'Update Flight' if self.instance and self.instance.pk else 'Log Flight'
        
        # Debug: Check what data is available in the instance
        if self.instance and self.instance.pk:
            print(f"DEBUG: Form instance has pk: {self.instance.pk}")
            print(f"DEBUG: night_time value: {self.instance.night_time} (type: {type(self.instance.night_time)})")
            print(f"DEBUG: ifr_time value: {self.instance.ifr_time} (type: {type(self.instance.ifr_time)})")
            print(f"DEBUG: pic_time value: {self.instance.pic_time} (type: {type(self.instance.pic_time)})")
        else:
            print("DEBUG: No instance or no pk - this is a new form")
        
        # Add total time to form context for fill buttons
        self.total_time_minutes = 0
        if self.instance and self.instance.pk and self.instance.total_time:
            self.total_time_minutes = int(self.instance.total_time * 60)
            
            # Handle aircraft data for existing flights
            if self.instance.aircraft:
                # Aircraft is selected - populate aircraft field
                self.fields['aircraft'].initial = self.instance.aircraft
        
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
                Column('pic_name', css_class='form-group col-md-12'),
                css_class='form-row'
            ),
            Row(
                Column('multi_pilot_time', css_class='form-group col-md-4'),
                Column('night_time', css_class='form-group col-md-4'),
                Column('ifr_time', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('day_landings', css_class='form-group col-md-4'),
                Column('night_landings', css_class='form-group col-md-4'),
                Column('ifr_approaches', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('pic_time', css_class='form-group col-md-4'),
                Column('copilot_time', css_class='form-group col-md-4'),
                Column('double_command_time', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('instructor_time', css_class='form-group col-md-6'),
                Column('simulator_type', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('simulator_time', css_class='form-group col-md-6'),
                Column('remarks', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
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
    

    



class AircraftForm(forms.ModelForm):
    """Form for creating and editing aircraft"""
    
    class Meta:
        model = Aircraft
        fields = ['registration', 'type', 'manufacturer', 'year_manufactured', 'engine_type']
        widgets = {
            'registration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'F-GABC'}),
            'type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cessna 152'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cessna'}),
            'year_manufactured': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2030'}),
            'engine_type': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Aircraft', css_class='btn btn-primary'))
        
        # Update aircraft field to include a "None" option
        self.fields['registration'].empty_label = "Select an aircraft from the list"
        self.fields['registration'].help_text = "Choose an aircraft from your registered aircraft, or leave blank to enter manually"


    
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
