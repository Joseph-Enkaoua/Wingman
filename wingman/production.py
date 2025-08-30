import os
from django.core.exceptions import ImproperlyConfigured
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else [
    'wingman.cyou',
    'www.wingman.cyou',
    '*.up.railway.app',
    '*.railway.app',
    'localhost',
    '127.0.0.1',
]

# CSRF trusted origins for HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://wingman.cyou',
    'https://www.wingman.cyou',
    'https://*.up.railway.app',
    'https://*.railway.app',
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL environment variable is not set. "
        "Please set it to your PostgreSQL connection string."
    )

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Simplified logging for production
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
