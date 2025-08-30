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
    echo "❌ ERROR: Using internal Railway hostname!"
    echo "   This will cause connection issues in deployment."
    echo ""
    echo "🔧 To fix this:"
    echo "1. Go to your Railway PostgreSQL service"
    echo "2. Click 'Connect' tab"
    echo "3. Copy the 'Public Endpoint' URL"
    echo "4. Update DATABASE_URL in your app's Variables"
    echo ""
    echo "Current DATABASE_URL format: $(echo $DATABASE_URL | sed 's/:[^:]*@/:***@/')"
    echo "Should be: postgresql://postgres:***@containers-us-west-XX.railway.app:XXXXX/railway"
    echo ""
    exit 1
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

# Run force migration script
echo "Running force migration script..."
python force_migrate.py || {
    echo "ERROR: Force migration failed!"
    echo "Trying alternative migration approach..."
    python manage.py migrate --run-syncdb --noinput
}

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

# Show migration status after
echo "Migration status after running migrations:"
python manage.py showmigrations

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "=== Railway deployment completed! ==="
