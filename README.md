# Wingman - Flight Logbook Application

A comprehensive Django web application for pilots and student pilots to log their flights, track progress, and generate professional logbooks in EASA/FAA format.

## ✈️ Features

### Flight Logging

- **Comprehensive Flight Entry**: Log flights with detailed information including aircraft, route, times, conditions, and pilot role
- **Auto-calculations**: Automatic calculation of total flight time from departure/arrival times
- **Time Breakdown**: Track night time, instrument time, cross-country time, and landings
- **Instructor Information**: Record instructor details for dual instruction flights
- **Remarks**: Add detailed notes and observations for each flight

### Aircraft Management

- **Fleet Management**: Add and manage multiple aircraft in your fleet
- **Aircraft Details**: Store registration, type, manufacturer, year, and total time
- **Usage Tracking**: Monitor which aircraft you fly most frequently

### Analytics & Charts

- **Dashboard**: Overview of flight statistics and recent flights
- **Progress Charts**: Visual representation of flight hours over time
- **Aircraft Usage**: Pie charts showing time distribution across aircraft
- **Flight Type Analysis**: Breakdown of different types of flights
- **Conditions Analysis**: VFR/IFR flight distribution

### Export & Reporting

- **PDF Export**: Generate professional logbooks in EASA/FAA format
- **Printable Reports**: Clean, formatted reports for licensing authorities
- **Data Export**: Export flight data for external analysis

### User Management

- **Pilot Profiles**: Store license information, medical details, and contact info
- **Flight School Integration**: Track instructor and flight school information
- **Profile Pictures**: Upload and manage pilot profile photos

## 🚀 Technology Stack

- **Backend**: Django 5.2.5
- **Frontend**: Bootstrap 5, Chart.js, Font Awesome
- **Database**: SQLite (development), PostgreSQL (production ready)
- **PDF Generation**: ReportLab
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Charts**: Chart.js for interactive visualizations

## 📋 Requirements

- Python 3.8+
- Django 5.2.5
- Additional packages (see requirements.txt)

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Wingman
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser**

   ```bash
   python manage.py createsuperuser
   ```

6. **Load sample data (optional)**

   ```bash
   python manage.py load_sample_data
   ```

7. **Run the development server**

   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000/`
   - Login with the sample user:
     - Username: `testpilot`
     - Password: `testpass123`

## 📱 Usage

### Getting Started

1. **Register/Login**: Create an account or use the sample user credentials
2. **Add Aircraft**: Start by adding aircraft to your fleet
3. **Log Your First Flight**: Use the intuitive flight logging form
4. **View Dashboard**: Check your progress and statistics
5. **Explore Charts**: Analyze your flying patterns and progress

### Flight Logging Process

1. Navigate to "Flights" → "Log New Flight"
2. Fill in the flight details:
   - Date and aircraft
   - Departure and arrival aerodromes
   - Times (auto-calculates total time)
   - Pilot role and conditions
   - Time breakdowns (night, instrument, cross-country)
   - Instructor information (if applicable)
   - Landings and remarks
3. Save the flight entry

### Key Features

- **Auto-calculation**: Total time is automatically calculated from departure/arrival times
- **Validation**: Form validates flight duration and required fields
- **Smart defaults**: Date defaults to today, times are user-friendly
- **Help tips**: Built-in guidance for proper flight logging

## 🎯 Target Users

- **Student Pilots**: Track training progress and meet licensing requirements
- **Private Pilots**: Maintain detailed flight records for currency and insurance
- **Commercial Pilots**: Professional logbook management for career advancement
- **Flight Schools**: Manage student progress and generate reports
- **Aviation Enthusiasts**: Document and analyze their flying experiences

## 📊 Sample Data

The application comes with sample data including:

- 3 aircraft (Cessna 152, Piper PA-28, Diamond DA40)
- 7 sample flights with various conditions and types
- Complete pilot profile with French aviation context
- Realistic flight routes in France (Paris, Strasbourg, Marseille)

## 🔧 Customization

### Adding New Aircraft Types

- Modify the `Aircraft` model in `logbook/models.py`
- Add new fields as needed for specific aircraft requirements

### Customizing Flight Types

- Update `FLIGHT_TYPE_CHOICES` in the `Flight` model
- Add new choices for specific aviation requirements

### Styling

- Customize the aviation theme in `templates/base.html`
- Modify colors and styling in the CSS section

## 📈 Future Enhancements

- **Mobile App**: Native iOS/Android applications
- **Weather Integration**: Automatic weather data for flights
- **Maintenance Tracking**: Aircraft maintenance and inspection records
- **Flight Planning**: Integration with flight planning tools
- **Social Features**: Share flights with other pilots
- **Advanced Analytics**: Machine learning insights and predictions
- **Multi-language Support**: International aviation community support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Aviation Community**: Inspired by the needs of real pilots and flight schools
- **Django Community**: Excellent framework and documentation
- **Bootstrap Team**: Beautiful and responsive UI components
- **Chart.js**: Powerful charting library for data visualization

## 📞 Support

For support, questions, or feature requests:

- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation for common questions

---

**Built with ❤️ for the aviation community**

_Wingman - Your trusted companion in the skies_
