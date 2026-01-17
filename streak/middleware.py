# streak/middleware.py
"""
Middleware để tự động ghi nhận streak khi user đã đăng nhập truy cập trang.
"""


class StreakMiddleware:
    """
    Middleware gọi register_login_streak cho mỗi authenticated request.
    Streak sẽ được cập nhật 1 lần/ngày dựa trên việc đăng nhập.
    """
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/jsi18n/',
        '/__debug__/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Chỉ xử lý nếu user đã login và không phải static files
        if hasattr(request, 'user') and request.user.is_authenticated:
            path = request.path
            # Skip các paths không cần track
            if not any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
                # Import ở đây để tránh circular import
                from streak.services import register_login_streak
                try:
                    register_login_streak(request.user)
                except Exception:
                    # Không để lỗi streak ảnh hưởng đến request
                    pass
        
        response = self.get_response(request)
        return response
