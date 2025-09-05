"""
Production-ready email service for Wingman Flight Logbook
Handles Gmail SMTP with proper timeout and error handling
"""
import threading
import time
import logging
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Production email service with async sending and retry logic"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def send_password_reset_email(self, user, reset_url):
        """
        Send password reset email with proper error handling
        """
        print(f"🔍 [DEBUG] Starting email send process for {user.email}")
        print(f"🔍 [DEBUG] Email config - HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
        print(f"🔍 [DEBUG] Email config - PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
        print(f"🔍 [DEBUG] Email config - USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
        print(f"🔍 [DEBUG] Email config - HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}")
        print(f"🔍 [DEBUG] Email config - FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
        try:
            print(f"🔍 [DEBUG] Step 1: Preparing email content")
            # Prepare email content
            subject = 'Password Reset Request - Wingman Flight Logbook'
            print(f"🔍 [DEBUG] Step 2: Rendering email template")
            message = render_to_string('logbook/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
            print(f"🔍 [DEBUG] Step 3: Template rendered successfully")
            
            print(f"🔍 [DEBUG] Step 4: Creating EmailMessage object")
            # Create email message
            email_msg = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email_msg.content_subtype = "html"
            print(f"🔍 [DEBUG] Step 5: EmailMessage created successfully")
            
            print(f"🔍 [DEBUG] Step 6: Starting background thread for email sending")
            # Send email in background thread to prevent timeouts
            thread = threading.Thread(
                target=self._send_email_async,
                args=(email_msg, user.email),
                daemon=True
            )
            thread.start()
            print(f"🔍 [DEBUG] Step 7: Background thread started successfully")
            
            logger.info(f'Password reset email queued for {user.email}')
            print(f"🔍 [DEBUG] Email queued successfully for {user.email}")
            return True
            
        except Exception as e:
            logger.error(f'Failed to queue password reset email for {user.email}: {str(e)}')
            print(f"❌ [DEBUG] Error in email queue process: {str(e)}")
            return False
    
    def _send_email_async(self, email_msg, recipient_email):
        """
        Send email asynchronously with retry logic
        """
        print(f"🔍 [DEBUG] Starting async email send for {recipient_email}")
        for attempt in range(self.max_retries):
            print(f"🔍 [DEBUG] Attempt {attempt + 1}/{self.max_retries} for {recipient_email}")
            try:
                print(f"🔍 [DEBUG] Setting socket timeout to 10 seconds")
                # Set socket timeout for this thread
                import socket
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)  # 10 second timeout
                print(f"🔍 [DEBUG] Socket timeout set, original was: {original_timeout}")
                
                try:
                    print(f"🔍 [DEBUG] About to call email_msg.send()")
                    email_msg.send(fail_silently=False)
                    print(f"🔍 [DEBUG] email_msg.send() completed successfully!")
                    logger.info(f'Password reset email sent successfully to {recipient_email}')
                    return True
                finally:
                    print(f"🔍 [DEBUG] Restoring original socket timeout")
                    socket.setdefaulttimeout(original_timeout)
                    
            except Exception as e:
                print(f"❌ [DEBUG] Email send attempt {attempt + 1} failed: {str(e)}")
                logger.warning(f'Email send attempt {attempt + 1} failed for {recipient_email}: {str(e)}')
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    print(f"🔍 [DEBUG] Waiting {wait_time} seconds before retry")
                    time.sleep(wait_time)  # Exponential backoff
                else:
                    print(f"❌ [DEBUG] All email send attempts failed for {recipient_email}")
                    logger.error(f'All email send attempts failed for {recipient_email}')
                    return False
        
        return False


# Global email service instance
email_service = EmailService()
