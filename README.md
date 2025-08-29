# ✈️ Wingman Flight Logbook

**Professional flight logging for pilots, built with Django**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Wingman.cyou-blue?style=for-the-badge&logo=airplane)](https://wingman.cyou)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2.5-green?style=flat&logo=django)](https://djangoproject.com)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple?style=flat&logo=bootstrap)](https://getbootstrap.com)

> **Live Demo:** [https://wingman.cyou](https://wingman.cyou)

A modern, comprehensive flight logbook application designed for pilots and flight schools. Track your flights, manage aircraft, generate professional reports, and analyze your aviation progress with beautiful charts and analytics.

## 🚀 Features

- **📝 Smart Flight Logging** - Auto-calculates times, validates data, EASA/FAA compliant
- **✈️ Aircraft Management** - Complete fleet tracking and usage analytics
- **📊 Interactive Dashboard** - Beautiful charts showing progress and statistics
- **📄 PDF Export** - Professional logbook generation for licensing authorities
- **👤 Pilot Profiles** - Store license info, medical details, and preferences
- **📱 Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **🔒 Secure & Private** - Your flight data is encrypted and secure

## 🛠️ Tech Stack

- **Backend:** Django 5.2.5, Python 3.8+
- **Frontend:** Bootstrap 5, Chart.js, Font Awesome
- **Database:** PostgreSQL (production), SQLite (development)
- **PDF Generation:** ReportLab
- **Deployment:** Railway, Heroku-ready

## 🎯 Perfect For

- **Student Pilots** - Track training progress and meet licensing requirements
- **Private Pilots** - Maintain detailed records for currency and insurance
- **Commercial Pilots** - Professional logbook management for career advancement
- **Flight Schools** - Manage student progress and generate reports

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/wingman.git
cd wingman

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py load_sample_data

# Start development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` and start logging your flights!

## 📸 Screenshots

<div align="center">
  <img src="https://via.placeholder.com/800x400/1e3a8a/ffffff?text=Dashboard+Preview" alt="Dashboard" width="400"/>
  <img src="https://via.placeholder.com/800x400/3b82f6/ffffff?text=Flight+Logging" alt="Flight Logging" width="400"/>
</div>

## 🌟 Key Features in Detail

### Smart Flight Logging

- **Auto-calculations** - Total time calculated from departure/arrival
- **Time breakdowns** - Night, instrument, cross-country, dual/solo
- **Validation** - Ensures accurate and compliant data entry
- **Remarks** - Add detailed notes and observations

### Beautiful Analytics

- **Progress charts** - Visual flight hours over time
- **Aircraft usage** - Pie charts showing fleet distribution
- **Flight type analysis** - Breakdown of different flight types
- **Conditions tracking** - VFR/IFR distribution

### Professional Export

- **PDF generation** - EASA/FAA compliant logbook format
- **Printable reports** - Clean formatting for authorities
- **Data export** - Export for external analysis

## 🔧 Customization

The application is highly customizable:

- **Aircraft types** - Add new fields for specific requirements
- **Flight types** - Customize for different aviation needs
- **Styling** - Modify the aviation theme and colors
- **Reports** - Customize PDF export format

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Live Demo:** [https://wingman.cyou](https://wingman.cyou)
- **Issues:** [GitHub Issues](https://github.com/yourusername/wingman/issues)
- **Email:** spie.system@gmail.com

---

<div align="center">

**Built with ❤️ for the aviation community**

_Wingman - Your trusted companion in the skies_

[![GitHub stars](https://img.shields.io/github/stars/yourusername/wingman?style=social)](https://github.com/yourusername/wingman)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/wingman?style=social)](https://github.com/yourusername/wingman)

</div>
