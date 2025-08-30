#!/usr/bin/env python
"""
Emergency migration script for Railway deployment
Run this manually if the release script fails to apply migrations
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection

def main():
    print("=== Emergency Migration Script ===")
    
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        print("ERROR: DATABASE_URL not set!")
        return
    
    print(f"DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Database connected: {version[0]}")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return
    
    # Check if auth_user table exists
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user;")
            count = cursor.fetchone()[0]
            print(f"auth_user table exists with {count} users")
    except Exception as e:
        print(f"auth_user table does not exist: {e}")
        print("Running migrations...")
        
        # Run migrations
        try:
            execute_from_command_line(['manage.py', 'migrate', '--noinput', '--verbosity=2'])
            print("Migrations completed successfully!")
        except Exception as e:
            print(f"Migration failed: {e}")
            return
    
    # Create superuser if no users exist
    from django.contrib.auth.models import User
    if not User.objects.exists():
        print("Creating superuser...")
        try:
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("Superuser created: admin/admin123")
        except Exception as e:
            print(f"Failed to create superuser: {e}")
    
    print("=== Emergency migration completed! ===")

if __name__ == '__main__':
    main()
