"""
Management command to debug email configuration and test Resend API
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from logbook.email_utils import test_resend_connection, send_email


class Command(BaseCommand):
    help = 'Debug email configuration and test Resend API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            type=str,
            help='Email address to send a test email to',
        )
        parser.add_argument(
            '--connection-only',
            action='store_true',
            help='Only test the connection, do not send test email',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Email Configuration Debug ===\n'))
        
        # Check environment variables
        self.stdout.write('1. Environment Variables:')
        resend_key = os.getenv('RESEND_API_KEY')
        default_from = os.getenv('DEFAULT_FROM_EMAIL')
        
        self.stdout.write(f'   RESEND_API_KEY: {"✓ Set" if resend_key else "✗ Not set"}')
        if resend_key:
            self.stdout.write(f'   RESEND_API_KEY (first 10 chars): {resend_key[:10]}...')
        
        self.stdout.write(f'   DEFAULT_FROM_EMAIL: {default_from or "Not set"}')
        
        # Check Django settings
        self.stdout.write('\n2. Django Settings:')
        self.stdout.write(f'   EMAIL_BACKEND: {getattr(settings, "EMAIL_BACKEND", "Not set")}')
        self.stdout.write(f'   DEFAULT_FROM_EMAIL (settings): {getattr(settings, "DEFAULT_FROM_EMAIL", "Not set")}')
        self.stdout.write(f'   SERVER_EMAIL: {getattr(settings, "SERVER_EMAIL", "Not set")}')
        
        # Test Resend connection
        self.stdout.write('\n3. Resend API Connection Test:')
        connection_result = test_resend_connection()
        
        if connection_result['api_key_present']:
            self.stdout.write('   ✓ API key is present')
        else:
            self.stdout.write('   ✗ API key is missing')
            
        if connection_result['api_key_valid']:
            self.stdout.write('   ✓ API key is valid')
        else:
            self.stdout.write('   ✗ API key is invalid or connection failed')
            
        if connection_result['domain_configured']:
            self.stdout.write(f'   ✓ Domain configured: {connection_result.get("configured_domain", "Unknown")}')
        else:
            self.stdout.write('   ✗ Domain not properly configured')
            
        if connection_result['error']:
            self.stdout.write(f'   ✗ Error: {connection_result["error"]}')
        
        # Send test email if requested
        if options['test_email'] and not options['connection_only']:
            self.stdout.write(f'\n4. Sending Test Email to {options["test_email"]}:')
            
            test_subject = "Wingman Email Test"
            test_html = """
            <html>
            <body>
                <h2>Email Test</h2>
                <p>This is a test email from your Wingman Flight Logbook application.</p>
                <p>If you receive this email, your email configuration is working correctly!</p>
                <p>Timestamp: {}</p>
            </body>
            </html>
            """.format(settings.TIME_ZONE)
            
            test_text = """
            Email Test
            
            This is a test email from your Wingman Flight Logbook application.
            
            If you receive this email, your email configuration is working correctly!
            """
            
            try:
                success = send_email(
                    to_email=options['test_email'],
                    subject=test_subject,
                    html_content=test_html,
                    text_content=test_text
                )
                
                if success:
                    self.stdout.write(self.style.SUCCESS('   ✓ Test email sent successfully!'))
                else:
                    self.stdout.write(self.style.ERROR('   ✗ Failed to send test email'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ Error sending test email: {str(e)}'))
        
        # Recommendations
        self.stdout.write('\n5. Recommendations:')
        
        if not connection_result['api_key_present']:
            self.stdout.write('   • Set the RESEND_API_KEY environment variable')
            
        if not connection_result['api_key_valid']:
            self.stdout.write('   • Check your Resend API key is correct and active')
            self.stdout.write('   • Verify your Resend account is in good standing')
            
        if not connection_result['domain_configured']:
            self.stdout.write('   • Set the DEFAULT_FROM_EMAIL environment variable')
            self.stdout.write('   • Verify your domain in the Resend dashboard')
            
        if connection_result['error']:
            self.stdout.write(f'   • Fix the connection error: {connection_result["error"]}')
        
        self.stdout.write('\n=== Debug Complete ===')
