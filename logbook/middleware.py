import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden

logger = logging.getLogger('django.security')


class SecurityMiddleware(MiddlewareMixin):
    """Custom security middleware for additional protection"""
    
    def process_request(self, request):
        # Log suspicious requests
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if self.is_suspicious_user_agent(user_agent):
            logger.warning(f'Suspicious User-Agent: {user_agent} from IP: {self.get_client_ip(request)}')
        
        # Block requests with suspicious headers
        if self.has_suspicious_headers(request):
            logger.warning(f'Suspicious headers from IP: {self.get_client_ip(request)}')
            return HttpResponseForbidden('Access denied')
        
        return None
    
    def process_response(self, request, response):
        # Add additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_suspicious_user_agent(self, user_agent):
        """Check for suspicious user agents"""
        suspicious_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'go-http-client', 'java-http-client'
        ]
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    def has_suspicious_headers(self, request):
        """Check for suspicious headers that might indicate attacks"""
        suspicious_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_X_CLIENT_IP',
            'HTTP_X_FORWARDED',
            'HTTP_FORWARDED_FOR_IP',
            'HTTP_VIA',
            'HTTP_X_COMING_FROM',
            'HTTP_COMING_FROM',
            'HTTP_X_FORWARDED_FOR_IP',
            'HTTP_X_REMOTE_ADDR',
            'HTTP_X_REMOTE_IP',
            'HTTP_X_CLUSTER_CLIENT_IP',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED',
            'HTTP_X_FORWARDED',
            'HTTP_FORWARDED_FOR_IP',
            'HTTP_VIA',
            'HTTP_X_COMING_FROM',
            'HTTP_COMING_FROM',
            'HTTP_X_FORWARDED_FOR_IP',
            'HTTP_X_REMOTE_ADDR',
            'HTTP_X_REMOTE_IP',
            'HTTP_X_CLUSTER_CLIENT_IP',
        ]
        
        # Check for multiple IP headers (potential IP spoofing)
        ip_headers = [request.META.get(header) for header in suspicious_headers if request.META.get(header)]
        return len(ip_headers) > 2  # More than 2 IP headers is suspicious
