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
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@wingman.cyou')
        
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
        
        # Send email via Resend
        response = resend.Emails.send(email_data)
        
        if response and hasattr(response, 'id'):
            logger.info(f'Email sent successfully via Resend. Email ID: {response.id}, To: {to_email}')
            return True
        else:
            logger.error(f'Failed to send email via Resend. Response: {response}')
            return False
            
    except Exception as e:
        logger.error(f'Error sending email via Resend to {to_email}: {str(e)}')
        return False


def send_email_via_django(to_email, subject, html_content, text_content=None, from_email=None):
    """
    Send email using Django's built-in email backend (fallback method)
    
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
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@wingman.cyou')
        
        # Send email via Django
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
    Send email using either Resend API or Django's email backend
    
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
    if use_resend and os.getenv('RESEND_API_KEY'):
        return send_email_via_resend(to_email, subject, html_content, text_content, from_email)
    else:
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
Hello {user.get_full_name() or user.username},

You're receiving this email because you requested a password reset for your Wingman Flight Logbook account.

Please click the link below to reset your password:
{reset_url}

If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.

This link will expire in 24 hours for security reasons.

Best regards,
The Wingman Team

---
This is an automated message, please do not reply to this email.
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
