import os
import dj_database_url
from .settings import *

# Debug: Print all environment variables to see what's available
print("DEBUG: All environment variables:")
for key, value in os.environ.items():
    if 'HOST' in key or 'SECRET' in key or 'DATABASE' in key:
        print(f"  {key}: {value}")
    elif key in ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'PORT']:
        print(f"  {key}: {value}")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')

# Update allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
# Debug: Print ALLOWED_HOSTS to see what's being read
print(f"DEBUG: ALLOWED_HOSTS environment variable: '{os.environ.get('ALLOWED_HOSTS', 'NOT_SET')}'")
print(f"DEBUG: ALLOWED_HOSTS list: {ALLOWED_HOSTS}")

# Fallback: If ALLOWED_HOSTS is empty or not set, use default Railway domains
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    print("DEBUG: ALLOWED_HOSTS is empty, using fallback values")
    ALLOWED_HOSTS = [
        'web-production-ce69e.up.railway.app',
        '*.up.railway.app', 
        '*.railway.app',
        'localhost',
        '127.0.0.1'
    ]

print(f"DEBUG: Final ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Add whitenoise middleware for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configure whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings (uncomment if using HTTPS)
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
