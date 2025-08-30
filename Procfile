web: echo "Starting deployment..." && python manage.py collectstatic --noinput --verbosity=2 && echo "Static files collected, starting server..." && gunicorn wingman.wsgi:application --log-level=info
