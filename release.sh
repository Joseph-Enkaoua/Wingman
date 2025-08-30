#!/bin/bash
# Simple Django deployment script for Railway

echo "=== Django Deployment ==="

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "=== Deployment complete ==="
