#!/bin/bash

# Startup script for Railway deployment

echo "Starting Wingman Flight Logbook..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn wingman.wsgi:application
