"""
URL configuration for wingman project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
import os

def serve_verification_file(request, filename):
    """Serve Google verification files from a dedicated secure directory"""
    # Construct the full filename
    full_filename = f"google{filename}.html"
    
    # Only allow files from the verification directory
    verification_dir = os.path.join(settings.BASE_DIR, 'static', 'verification')
    file_path = os.path.join(verification_dir, full_filename)
    
    # Security: ensure file is actually in the verification directory (prevent path traversal)
    if not os.path.abspath(file_path).startswith(os.path.abspath(verification_dir)):
        return HttpResponse('Not found', status=404)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Not found', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('logbook.urls')),
    
    # SEO URLs
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('sitemap.xml', TemplateView.as_view(template_name='sitemap.xml', content_type='application/xml')),
    
    # Google verification files (e.g., googleec06e69f186856f7.html)
    path('google<str:filename>.html', serve_verification_file, name='verification_file'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
