#!/usr/bin/env python
"""
Test script to verify email configuration
Run this on Railway to test if emails are working
"""

import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
django.setup()

def test_email():
    """Test sending an email"""
    try:
        print("Testing email configuration...")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Test sending email
        send_mail(
            'Test Email from Wingman',
            'This is a test email to verify the configuration is working.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Send to yourself for testing
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        print(f"Error type: {type(e).__name__}")

if __name__ == '__main__':
    test_email()
