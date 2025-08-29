#!/bin/bash
# Release script for Railway deployment

echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Release script completed!"
