#!/bin/bash
# Enhanced Django deployment script for Railway

echo "=== Django Deployment ==="

# Check if database is accessible
echo "Checking database connection..."
python manage.py check --database default

# Check migration status
echo "Checking migration status..."
python manage.py showmigrations

# Run migrations with better error handling
echo "Running migrations..."
python manage.py migrate --noinput

# If migrations fail, try to reset and re-run
if [ $? -ne 0 ]; then
    echo "Migration failed. Attempting to reset migration state..."
    python manage.py migrate --fake auth zero || true
    python manage.py migrate --fake admin zero || true
    python manage.py migrate --fake contenttypes zero || true
    python manage.py migrate --fake sessions zero || true
    python manage.py migrate --fake logbook zero || true
    
    echo "Running migrations again..."
    python manage.py migrate --noinput
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional)
echo "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Creating one...')
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('Superuser created: admin/changeme123')
else:
    print('Superuser already exists')
"

echo "=== Deployment complete ==="
