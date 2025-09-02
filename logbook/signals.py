import logging
from django.contrib.auth.signals import user_login_failed, user_logged_in, user_logged_out
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.exceptions import ValidationError

logger = logging.getLogger('logbook')

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts from Django's built-in authentication"""
    username = credentials.get('username', 'unknown')
    ip = get_client_ip(request)
    logger.warning(f'*** FAILED LOGIN ATTEMPT *** for username: {username} from IP: {ip}')

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Log successful logins from Django's built-in authentication"""
    ip = get_client_ip(request)
    logger.info(f'Django built-in auth successful login for user: {user.username} from IP: {ip}')

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    """Log user logouts"""
    if user:
        ip = get_client_ip(request)
        logger.info(f'User logout: {user.username} from IP: {ip}')

def get_client_ip(request):
    """Get client IP for logging purposes"""
    if not request:
        return 'unknown'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


from django.db.models.signals import pre_save, post_save

@receiver(pre_save, sender=User)
def ensure_email_uniqueness(sender, instance, **kwargs):
    """Ensure email uniqueness for users before saving"""
    if instance.email:
        # Check if another user has this email (excluding current user)
        if User.objects.filter(email=instance.email).exclude(pk=instance.pk).exists():
            raise ValidationError("A user with this email already exists.")

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log when new users are created"""
    if created:
        logger.info(f'New user created: {instance.username} with email: {instance.email}')
        # Create pilot profile automatically
        from .models import PilotProfile
        PilotProfile.objects.get_or_create(user=instance)
