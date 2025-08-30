#!/bin/bash

# Exit on any error
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Release phase completed successfully!"
