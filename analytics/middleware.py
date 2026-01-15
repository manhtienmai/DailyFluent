import re
from django.utils import timezone


# Paths to exclude from tracking
EXCLUDED_PATHS = [
    r'^/admin/',
    r'^/static/',
    r'^/media/',
    r'^/__debug__/',
    r'^/favicon\.ico$',
    r'\.map$',
    r'\.js$',
    r'\.css$',
    r'\.png$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.gif$',
    r'\.svg$',
    r'\.woff',
    r'\.ttf',
]

EXCLUDED_PATTERNS = [re.compile(p) for p in EXCLUDED_PATHS]


def get_client_ip(request):
    """Get client IP from request, handling proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent):
    """Simple user agent parser"""
    browser = "Unknown"
    device = "Desktop"
    os_name = "Unknown"
    
    ua_lower = user_agent.lower()
    
    # Detect browser
    if 'chrome' in ua_lower and 'edg' not in ua_lower:
        browser = "Chrome"
    elif 'firefox' in ua_lower:
        browser = "Firefox"
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        browser = "Safari"
    elif 'edg' in ua_lower:
        browser = "Edge"
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        browser = "Opera"
    
    # Detect device
    if 'mobile' in ua_lower or 'android' in ua_lower and 'tablet' not in ua_lower:
        device = "Mobile"
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        device = "Tablet"
    
    # Detect OS
    if 'windows' in ua_lower:
        os_name = "Windows"
    elif 'mac os' in ua_lower or 'macos' in ua_lower:
        os_name = "macOS"
    elif 'linux' in ua_lower:
        os_name = "Linux"
    elif 'android' in ua_lower:
        os_name = "Android"
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        os_name = "iOS"
    
    return browser, device, os_name


class AnalyticsMiddleware:
    """Middleware to track page views"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only track successful GET requests
        if request.method != 'GET':
            return response
        
        if response.status_code != 200:
            return response
        
        # Check excluded paths
        path = request.path
        for pattern in EXCLUDED_PATTERNS:
            if pattern.search(path):
                return response
        
        # Track async to avoid slowing down response
        try:
            self._track_pageview(request)
        except Exception:
            pass  # Don't let analytics errors affect the site
        
        return response
    
    def _track_pageview(self, request):
        from analytics.models import PageView
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        browser, device, os_name = parse_user_agent(user_agent)
        
        PageView.objects.create(
            path=request.path,
            user=request.user if request.user.is_authenticated else None,
            ip_address=get_client_ip(request),
            user_agent=user_agent[:500] if user_agent else '',
            referer=request.META.get('HTTP_REFERER', '')[:1000],
            browser=browser,
            device=device,
            os=os_name,
        )
