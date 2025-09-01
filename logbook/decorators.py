import logging
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger('logbook')

def login_required_with_logging(view_func):
    """Custom login_required decorator that logs authentication failures"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            # Log unauthorized access attempt
            ip = get_client_ip(request)
            path = request.path
            logger.warning(f'Unauthorized access attempt to {path} from IP: {ip}')
            return redirect(reverse('login'))
    return wrapper

def get_client_ip(request):
    """Get client IP for logging purposes"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
