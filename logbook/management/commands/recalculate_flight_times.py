from django.core.management.base import BaseCommand
from logbook.models import Flight


class Command(BaseCommand):
    help = 'Recalculate all flight times using the new accurate calculation method and update engine time accordingly'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        flights = Flight.objects.all()
        dry_run = options['dry_run']
        
        self.stdout.write(f"Found {flights.count()} flights to process...")
        
        updated_count = 0
        errors = []
        
        for flight in flights:
            if flight.departure_time and flight.arrival_time:
                old_time = flight.total_time
                exact_minutes = flight.exact_flight_minutes
                new_time = round(exact_minutes / 60, 2)
                
                if abs(float(old_time) - new_time) > 0.01:  # If difference is more than 0.01 hours
                    updated_count += 1  # Count for both dry-run and actual updates
                    if dry_run:
                        self.stdout.write(
                            f"Flight {flight.id} ({flight.date}): "
                            f"{flight.departure_time} - {flight.arrival_time} = "
                            f"{old_time:.2f}h -> {new_time:.2f}h "
                            f"({exact_minutes} minutes)"
                        )
                    else:
                        try:
                            flight.total_time = new_time
                            # Use full save() to trigger engine time recalculation
                            flight.save()
                            self.stdout.write(
                                f"Updated Flight {flight.id}: {old_time:.2f}h -> {new_time:.2f}h"
                            )
                        except Exception as e:
                            errors.append(f"Flight {flight.id}: {str(e)}")
                else:
                    if dry_run:
                        self.stdout.write(
                            f"Flight {flight.id}: {old_time:.2f}h (no change needed)"
                        )
            else:
                if dry_run:
                    self.stdout.write(f"Flight {flight.id}: Missing departure or arrival time")
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDRY RUN: Would update {updated_count} flights"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully updated {updated_count} flights"
                )
            )
            
            if errors:
                self.stdout.write(
                    self.style.ERROR(f"\nErrors encountered: {len(errors)}")
                )
                for error in errors:
                    self.stdout.write(self.style.ERROR(f"  {error}"))
