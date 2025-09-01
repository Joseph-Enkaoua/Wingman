from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    path('charts/', views.charts_view, name='charts'),
    path('charts/print/', views.print_charts_view, name='print-charts'),
    path('profile/', views.profile_view, name='profile'),
    
    # Flight management
    path('flights/', views.FlightListView.as_view(), name='flight-list'),
    path('flights/new/', views.FlightCreateView.as_view(), name='flight-create'),
    path('flights/<int:pk>/', views.FlightDetailView.as_view(), name='flight-detail'),
    path('flights/<int:pk>/edit/', views.FlightUpdateView.as_view(), name='flight-update'),
    path('flights/<int:pk>/delete/', views.FlightDeleteView.as_view(), name='flight-delete'),
    
    # Aircraft management
    path('aircraft/', views.AircraftListView.as_view(), name='aircraft-list'),
    path('aircraft/new/', views.AircraftCreateView.as_view(), name='aircraft-create'),
    path('aircraft/<int:pk>/edit/', views.AircraftUpdateView.as_view(), name='aircraft-update'),
    path('aircraft/<int:pk>/delete/', views.AircraftDeleteView.as_view(), name='aircraft-delete'),
    
    # Export and API
    path('export/pdf/', views.export_pdf, name='export-pdf'),
    path('export/csv/', views.export_csv, name='export-csv'),
    path('api/stats/', views.api_flight_stats, name='api-stats'),
    
    # Legal pages
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
]
