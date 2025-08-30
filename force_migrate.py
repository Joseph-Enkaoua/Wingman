#!/usr/bin/env python
"""
Force Migration Script for Railway
This script forces database initialization and migration
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection, transaction
from django.contrib.auth.models import User

def main():
    print("=== Force Migration Script ===")
    
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        print("ERROR: DATABASE_URL not set!")
        return
    
    print(f"Using DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Connected to PostgreSQL: {version[0]}")
        
        # Check if auth_user table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'auth_user'
                );
            """)
            table_exists = cursor.fetchone()[0]
            print(f"auth_user table exists: {table_exists}")
        
        if not table_exists:
            print("auth_user table does not exist. Running migrations...")
            
            # Run migrations
            print("Running Django migrations...")
            execute_from_command_line(['manage.py', 'migrate', '--noinput'])
            
            # Verify auth_user table was created
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'auth_user'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                print(f"auth_user table exists after migration: {table_exists}")
            
            if table_exists:
                print("✅ Migrations completed successfully!")
                
                # Create a superuser if none exists
                if not User.objects.filter(is_superuser=True).exists():
                    print("Creating superuser...")
                    User.objects.create_superuser(
                        username='admin',
                        email='admin@example.com',
                        password='admin123'
                    )
                    print("✅ Superuser created: admin/admin123")
                else:
                    print("Superuser already exists")
            else:
                print("❌ Migrations failed - auth_user table still doesn't exist")
        else:
            print("✅ auth_user table already exists")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
