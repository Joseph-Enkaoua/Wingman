"""
Management command to test email sending functionality
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from logbook.email_utils import send_email, send_password_reset_email, send_welcome_email


class Command(BaseCommand):
    help = 'Test email sending functionality with Resend'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['test', 'welcome', 'password-reset'],
            default='test',
            help='Type of email to send',
        )

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']

        if not email:
            # Use the first user's email if no email provided
            try:
                user = User.objects.first()
                if user and user.email:
                    email = user.email
                else:
                    self.stdout.write(
                        self.style.ERROR('No email provided and no users found with email addresses.')
                    )
                    return
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('No users found in the database.')
                )
                return

        self.stdout.write(f'Sending {email_type} email to {email}...')

        try:
            if email_type == 'test':
                success = send_email(
                    to_email=email,
                    subject="Test Email from Wingman",
                    html_content="""
                    <html>
                    <body>
                        <h2>Test Email</h2>
                        <p>This is a test email from your Wingman Flight Logbook application.</p>
                        <p>If you're receiving this, your email configuration is working correctly!</p>
                        <p>Best regards,<br>Wingman Team</p>
                    </body>
                    </html>
                    """,
                    text_content="""
Test Email

This is a test email from your Wingman Flight Logbook application.

If you're receiving this, your email configuration is working correctly!

Best regards,
Wingman Team
                    """
                )

            elif email_type == 'welcome':
                try:
                    user = User.objects.get(email=email)
                    success = send_welcome_email(user)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'No user found with email {email}')
                    )
                    return

            elif email_type == 'password-reset':
                try:
                    user = User.objects.get(email=email)
                    # Create a dummy reset URL for testing
                    reset_url = "https://example.com/reset-password/test-token"
                    success = send_password_reset_email(user, reset_url)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'No user found with email {email}')
                    )
                    return

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {email_type.title()} email sent successfully to {email}!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send {email_type} email to {email}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error sending email: {str(e)}')
            )
