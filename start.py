#!/usr/bin/env python3
"""
Startup script for Railway deployment
"""

import os
import sys
import subprocess
import django

def main():
    print("Starting Wingman Flight Logbook...")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
    
    try:
        django.setup()
        print("Django setup completed")
    except Exception as e:
        print(f"Error setting up Django: {e}")
        sys.exit(1)
    
    # Collect static files
    print("Collecting static files...")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("Static files collected successfully")
    except Exception as e:
        print(f"Error collecting static files: {e}")
        # Don't exit here, continue with server startup
    
    # Start Gunicorn
    print("Starting Gunicorn server...")
    try:
        # Use exec to replace the current process
        os.execvp('gunicorn', ['gunicorn', 'wingman.wsgi:application'])
    except Exception as e:
        print(f"Error starting Gunicorn: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
