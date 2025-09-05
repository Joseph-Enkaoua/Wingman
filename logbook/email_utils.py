"""
Email utility functions for sending emails via Resend
"""
import os
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
import resend

logger = logging.getLogger(__name__)

# Initialize Resend with API key
resend.api_key = os.getenv('RESEND_API_KEY')


def test_resend_connection():
    """
    Test the Resend API connection and configuration
    
    Returns:
        dict: Test results with status and details
    """
    result = {
        'api_key_present': bool(os.getenv('RESEND_API_KEY')),
        'api_key_valid': False,
        'domain_configured': False,
        'error': None
    }
    
    try:
        if not result['api_key_present']:
            result['error'] = 'RESEND_API_KEY environment variable is not set'
            return result
        
        # Test API key by making a simple request
        # We'll try to get domains to test the connection
        try:
            domains = resend.Domains.list()
            result['api_key_valid'] = True
            logger.info('Resend API connection test successful')
        except Exception as e:
            result['error'] = f'Resend API connection failed: {str(e)}'
            logger.error(f'Resend API connection test failed: {str(e)}')
            return result
        
        # Check if we have a configured domain
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@wingman.cyou')
        if '@' in default_from:
            domain = default_from.split('@')[1]
            result['domain_configured'] = True
            result['configured_domain'] = domain
            logger.info(f'Using domain: {domain}')
        
        return result
        
    except Exception as e:
        result['error'] = f'Unexpected error during Resend connection test: {str(e)}'
        logger.error(f'Unexpected error during Resend connection test: {str(e)}')
        return result


def send_email_via_resend(to_email, subject, html_content, text_content=None, from_email=None):
    """
    Send email using Resend API
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
        text_content (str, optional): Plain text content of the email
        from_email (str, optional): Sender email address
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Check if API key is available
        if not resend.api_key:
            logger.error('Resend API key is not set. Please check RESEND_API_KEY environment variable.')
            return False
            
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@mail.wingman.cyou')
        
        # Log the attempt with sanitized data
        logger.info(f'Attempting to send email via Resend to {to_email} from {from_email}')
        
        # Prepare email data
        email_data = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Add text content if provided
        if text_content:
            email_data["text"] = text_content
        
        # Add Reply-To header to improve deliverability and trust
        # This allows recipients to reply to emails, increasing trust
        reply_to_email = getattr(settings, 'REPLY_TO_EMAIL', 'support@mail.wingman.cyou')
        email_data["reply_to"] = reply_to_email
        
        # Add headers for better deliverability
        email_data["headers"] = {
            "X-Mailer": "Wingman Flight Logbook",
            "X-Priority": "3",  # Normal priority
        }
        
        # Log email data (without sensitive content)
        logger.debug(f'Email data prepared: from={from_email}, to={to_email}, subject={subject}')
        
        # Send email via Resend
        response = resend.Emails.send(email_data)
        
        # Log the full response for debugging
        logger.debug(f'Resend API response: {response}')
        
        if response and hasattr(response, 'id'):
            logger.info(f'Email sent successfully via Resend. Email ID: {response.id}, To: {to_email}')
            return True
        else:
            logger.error(f'Failed to send email via Resend. Response: {response}')
            return False
            
    except Exception as e:
        # Enhanced error logging
        error_msg = str(e)
        error_type = type(e).__name__
        
        logger.error(f'Error sending email via Resend to {to_email}: {error_type}: {error_msg}')
        
        # Log additional context for debugging
        logger.error(f'Email context - From: {from_email}, Subject: {subject}')
        logger.error(f'Resend API key present: {bool(resend.api_key)}')
        
        # Check for specific error types
        if '401' in error_msg or 'unauthorized' in error_msg.lower():
            logger.error('Resend API authentication failed. Check your API key.')
        elif '403' in error_msg or 'forbidden' in error_msg.lower():
            logger.error('Resend API access forbidden. Check your domain verification and API permissions.')
        elif '429' in error_msg or 'rate limit' in error_msg.lower():
            logger.error('Resend API rate limit exceeded.')
        elif '422' in error_msg or 'validation' in error_msg.lower():
            logger.error('Resend API validation error. Check email format and content.')
        
        return False


def send_email_via_django(to_email, subject, html_content, text_content=None, from_email=None):
    """
    Send email using Django's built-in email backend (development only)
    
    This function is only used in development when EMAIL_BACKEND is set to console.
    In production, all emails are sent via Resend API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
        text_content (str, optional): Plain text content of the email
        from_email (str, optional): Sender email address
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@mail.wingman.cyou')
        
        # Send email via Django (will print to console in development)
        send_mail(
            subject=subject,
            message=text_content or html_content,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False
        )
        
        logger.info(f'Email sent successfully via Django to {to_email}')
        return True
        
    except Exception as e:
        logger.error(f'Error sending email via Django to {to_email}: {str(e)}')
        return False


def send_email(to_email, subject, html_content, text_content=None, from_email=None, use_resend=True):
    """
    Send email using Resend API (production) or Django console backend (development)
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
        text_content (str, optional): Plain text content of the email
        from_email (str, optional): Sender email address
        use_resend (bool): Whether to use Resend API (True) or Django backend (False)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # In production: Always use Resend API if configured
    if use_resend and os.getenv('RESEND_API_KEY'):
        logger.info(f'Attempting to send email via Resend to {to_email}')
        return send_email_via_resend(to_email, subject, html_content, text_content, from_email)
    else:
        # In development: Use Django console backend for logging
        logger.info(f'Sending email via Django console backend to {to_email}')
        return send_email_via_django(to_email, subject, html_content, text_content, from_email)


def send_password_reset_email(user, reset_url):
    """
    Send password reset email to user
    
    Args:
        user: Django User object
        reset_url (str): Password reset URL
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Render email template
        html_content = render_to_string('logbook/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url
        })
        
        # Create plain text version
        text_content = f"""
PASSWORD RESET REQUEST - WINGMAN FLIGHT LOGBOOK

Hello {user.get_full_name() or user.username},

You're receiving this email because you requested a password reset for your Wingman Flight Logbook account.

TO RESET YOUR PASSWORD:
Click the link below or copy and paste it into your browser:
{reset_url}

IMPORTANT SECURITY INFORMATION:
- This link will expire in 24 hours for security reasons
- If you didn't request this password reset, you can safely ignore this email
- Your password will remain unchanged unless you use the link above

If you have any questions or need assistance, please contact our support team.

Best regards,
The Wingman Team

---
This email was sent from Wingman Flight Logbook ({user.email})
If you have questions, please reply to this email or contact us at support@mail.wingman.cyou
        """
        
        subject = "Password Reset Request - Wingman Flight Logbook"
        
        return send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
    except Exception as e:
        logger.error(f'Error sending password reset email to {user.email}: {str(e)}')
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user
    
    Args:
        user: Django User object
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Wingman Flight Logbook!</h2>
            <p>Hello {user.get_full_name() or user.username},</p>
            <p>Thank you for joining Wingman Flight Logbook! We're excited to help you track your flight hours and maintain your pilot logbook.</p>
            <p>You can now:</p>
            <ul>
                <li>Log your flights with detailed information</li>
                <li>Track your flight hours and experience</li>
                <li>Generate reports and charts</li>
                <li>Export your logbook to PDF or CSV</li>
            </ul>
            <p>If you have any questions, feel free to reach out to our support team.</p>
            <p>Happy flying!</p>
            <p>Best regards,<br>The Wingman Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
Welcome to Wingman Flight Logbook!

Hello {user.get_full_name() or user.username},

Thank you for joining Wingman Flight Logbook! We're excited to help you track your flight hours and maintain your pilot logbook.

You can now:
- Log your flights with detailed information
- Track your flight hours and experience
- Generate reports and charts
- Export your logbook to PDF or CSV

If you have any questions, feel free to reach out to our support team.

Happy flying!

Best regards,
The Wingman Team
        """
        
        subject = "Welcome to Wingman Flight Logbook!"
        
        return send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
    except Exception as e:
        logger.error(f'Error sending welcome email to {user.email}: {str(e)}')
        return False
