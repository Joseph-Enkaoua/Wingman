#!/bin/bash
# Release script for Railway deployment

echo "=== Starting Railway deployment ==="

# Check if we're in the right directory
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Check database connection
echo "Testing database connection..."
python manage.py check --database default

# Show migration status
echo "Current migration status:"
python manage.py showmigrations

# Run migrations with verbose output
echo "Running Django migrations..."
python manage.py migrate --noinput --verbosity=2

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
