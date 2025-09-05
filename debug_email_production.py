#!/usr/bin/env python3
"""
Script to debug email configuration in production
Run this script to test your email setup and identify issues
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wingman.production')
django.setup()

from logbook.email_utils import test_resend_connection, send_email
from django.conf import settings

def main():
    print("=== Wingman Email Configuration Debug ===\n")
    
    # Check environment variables
    print("1. Environment Variables:")
    resend_key = os.getenv('RESEND_API_KEY')
    default_from = os.getenv('DEFAULT_FROM_EMAIL')
    
    print(f"   RESEND_API_KEY: {'✓ Set' if resend_key else '✗ Not set'}")
    if resend_key:
        print(f"   RESEND_API_KEY (first 10 chars): {resend_key[:10]}...")
    
    print(f"   DEFAULT_FROM_EMAIL: {default_from or 'Not set'}")
    
    # Check Django settings
    print("\n2. Django Settings:")
    print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"   DEFAULT_FROM_EMAIL (settings): {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"   SERVER_EMAIL: {getattr(settings, 'SERVER_EMAIL', 'Not set')}")
    
    # Test Resend connection
    print("\n3. Resend API Connection Test:")
    connection_result = test_resend_connection()
    
    if connection_result['api_key_present']:
        print("   ✓ API key is present")
    else:
        print("   ✗ API key is missing")
        
    if connection_result['api_key_valid']:
        print("   ✓ API key is valid")
    else:
        print("   ✗ API key is invalid or connection failed")
        
    if connection_result['domain_configured']:
        print(f"   ✓ Domain configured: {connection_result.get('configured_domain', 'Unknown')}")
    else:
        print("   ✗ Domain not properly configured")
        
    if connection_result['error']:
        print(f"   ✗ Error: {connection_result['error']}")
    
    # Test email sending
    print("\n4. Test Email Sending:")
    test_email = input("Enter email address to send test email to (or press Enter to skip): ").strip()
    
    if test_email:
        print(f"   Sending test email to {test_email}...")
        
        test_subject = "Wingman Email Test"
        test_html = """
        <html>
        <body>
            <h2>Email Test</h2>
            <p>This is a test email from your Wingman Flight Logbook application.</p>
            <p>If you receive this email, your email configuration is working correctly!</p>
        </body>
        </html>
        """
        
        test_text = """
        Email Test
        
        This is a test email from your Wingman Flight Logbook application.
        
        If you receive this email, your email configuration is working correctly!
        """
        
        try:
            success = send_email(
                to_email=test_email,
                subject=test_subject,
                html_content=test_html,
                text_content=test_text
            )
            
            if success:
                print("   ✓ Test email sent successfully!")
            else:
                print("   ✗ Failed to send test email")
                
        except Exception as e:
            print(f"   ✗ Error sending test email: {str(e)}")
    
    # Recommendations
    print("\n5. Recommendations:")
    
    if not connection_result['api_key_present']:
        print("   • Set the RESEND_API_KEY environment variable")
        
    if not connection_result['api_key_valid']:
        print("   • Check your Resend API key is correct and active")
        print("   • Verify your Resend account is in good standing")
        
    if not connection_result['domain_configured']:
        print("   • Set the DEFAULT_FROM_EMAIL environment variable")
        print("   • Verify your domain in the Resend dashboard")
        
    if connection_result['error']:
        print(f"   • Fix the connection error: {connection_result['error']}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    main()
