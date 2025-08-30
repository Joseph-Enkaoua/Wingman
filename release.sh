#!/bin/bash
# Release script for Railway deployment

set -e  # Exit on any error

echo "=== Starting Railway deployment ==="

# Check if we're in the right directory
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Set Django settings to production
export DJANGO_SETTINGS_MODULE=wingman.production
echo "Using Django settings: $DJANGO_SETTINGS_MODULE"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set!"
    exit 1
fi
echo "DATABASE_URL is set"

# Check database connection
echo "Testing database connection..."
python manage.py check --database default || {
    echo "ERROR: Database connection failed!"
    exit 1
}

# Show migration status
echo "Current migration status:"
python manage.py showmigrations

# Force run all migrations
echo "Running Django migrations..."
python manage.py migrate --noinput --verbosity=2 --run-syncdb

# Double-check that auth_user table exists
echo "Verifying auth_user table exists..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT COUNT(*) FROM auth_user\")
    count = cursor.fetchone()[0]
    print(f'auth_user table exists with {count} users')
"

# Initialize database if needed
echo "Initializing database..."
python manage.py init_database

# Show migration status after
echo "Migration status after running migrations:"
python manage.py showmigrations

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "=== Railway deployment completed! ==="
