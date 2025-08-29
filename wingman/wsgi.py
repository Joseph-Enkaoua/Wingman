"""
WSGI config for wingman project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use production settings in production environment
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DJANGO_SETTINGS_MODULE') == 'wingman.production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
    print("DEBUG: Using production settings")
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.settings')
    print("DEBUG: Using development settings")

print(f"DEBUG: DJANGO_SETTINGS_MODULE will be: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

application = get_wsgi_application()
