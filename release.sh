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

# Show DATABASE_URL (masked for security)
echo "DATABASE_URL format: $(echo $DATABASE_URL | sed 's/:[^:]*@/:***@/')"

# Check if it's an internal Railway URL
if [[ "$DATABASE_URL" == *"railway.internal"* ]]; then
    echo "WARNING: Using internal Railway hostname. This might not work in all environments."
    echo "Consider using the public PostgreSQL endpoint instead."
fi

# Check database connection
echo "Testing database connection..."
python manage.py check --database default || {
    echo "ERROR: Database connection failed!"
    echo "This might be due to:"
    echo "1. PostgreSQL service not running"
    echo "2. Wrong DATABASE_URL format"
    echo "3. Network connectivity issues"
    echo ""
    echo "Trying alternative connection methods..."
    
    # Try to connect with basic psql command to test connectivity
    if command -v psql &> /dev/null; then
        echo "Testing with psql..."
        psql "$DATABASE_URL" -c "SELECT version();" || {
            echo "psql connection also failed"
            echo "Please check your Railway PostgreSQL service configuration"
            exit 1
        }
    fi
    
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
