from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Initialize the database with all migrations and create a superuser if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-initialization even if tables exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database initialization...'))
        
        # Check if we're in production
        is_production = os.environ.get('DATABASE_URL') is not None
        
        if is_production:
            self.stdout.write('Production environment detected')
        else:
            self.stdout.write('Development environment detected')
        
        # Check if tables exist
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auth_user'
            """)
            tables_exist = cursor.fetchone() is not None
        
        if tables_exist and not options['force']:
            self.stdout.write(self.style.WARNING('Tables already exist. Use --force to re-initialize.'))
            return
        
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=1)
        
        # Create superuser if in production and no users exist
        if is_production:
            if not User.objects.exists():
                self.stdout.write('Creating superuser...')
                # Create a default superuser
                username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
                email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
                password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
                
                try:
                    User.objects.create_superuser(username, email, password)
                    self.stdout.write(
                        self.style.SUCCESS(f'Superuser created: {username}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to create superuser: {e}')
                    )
            else:
                self.stdout.write('Users already exist, skipping superuser creation')
        
        # Load sample data if in development
        if not is_production:
            try:
                self.stdout.write('Loading sample data...')
                call_command('load_sample_data')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not load sample data: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('Database initialization completed!'))
