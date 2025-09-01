import logging
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib import messages

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

def adaptive_ratelimit(rate='1000/h', key='user', method='ALL', block=False):
    """
    Adaptive rate limiting decorator that applies different limits based on user authentication status.
    
    Args:
        rate: Rate limit for logged-in users (default: 1000/hour)
        key: Rate limiting key ('user', 'ip', or 'user_or_ip')
        method: HTTP method to apply rate limiting to
        block: Whether to block requests when rate limit is exceeded
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Apply rate limiting based on user authentication status
            if request.user.is_authenticated:
                # Logged-in users get the specified rate limit
                rate_limit = rate
            else:
                # Anonymous users get stricter rate limits
                rate_limit = getattr(settings, 'RATELIMIT_ANONYMOUS', '100/h')
            
            # Apply the rate limit
            @ratelimit(key=key, rate=rate_limit, method=method, block=block)
            def rate_limited_view(request, *args, **kwargs):
                return view_func(request, *args, **kwargs)
            
            # Check if rate limit was exceeded
            was_limited = getattr(request, 'limited', False)
            if was_limited:
                if request.user.is_authenticated:
                    logger.warning(f'Rate limit exceeded for authenticated user: {request.user.username}')
                    messages.error(request, 'Rate limit exceeded. Please slow down your requests.')
                else:
                    logger.warning(f'Rate limit exceeded for anonymous user from IP: {request.META.get("REMOTE_ADDR")}')
                    messages.error(request, 'Rate limit exceeded. Please log in or slow down your requests.')
                
                if block:
                    return HttpResponseForbidden('Rate limit exceeded')
            
            return rate_limited_view(request, *args, **kwargs)
        return wrapped_view
    return decorator

def user_ratelimit(rate='1000/h', key='user', method='ALL', block=False):
    """
    Rate limiting decorator specifically for authenticated users only.
    Skips rate limiting for anonymous users.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Only apply rate limiting to authenticated users
                @ratelimit(key=key, rate=rate, method=method, block=block)
                def rate_limited_view(request, *args, **kwargs):
                    return view_func(request, *args, **kwargs)
                
                # Check if rate limit was exceeded
                was_limited = getattr(request, 'limited', False)
                if was_limited:
                    logger.warning(f'Rate limit exceeded for authenticated user: {request.user.username}')
                    messages.error(request, 'Rate limit exceeded. Please slow down your requests.')
                    
                    if block:
                        return HttpResponseForbidden('Rate limit exceeded')
                
                return rate_limited_view(request, *args, **kwargs)
            else:
                # Anonymous users bypass rate limiting
                return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
