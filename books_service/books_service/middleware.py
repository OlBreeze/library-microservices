"""
Middleware для логування та обробки помилок.
"""
import logging
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('books_service')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Логування всіх запитів до Books Service.
    """

    def process_request(self, request):
        """Логує вхідний запит."""
        request.start_time = time.time()

        # Логуємо тільки захищені ендпоінти
        if request.path.startswith('/api/books/'):
            logger.info(
                f"📥 {request.method} {request.path} | "
                f"User: {getattr(request.user, 'username', 'Anonymous')} | "
                f"IP: {self.get_client_ip(request)}"
            )

    def process_response(self, request, response):
        """Логує відповідь з часом виконання."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            status_emoji = "✅" if response.status_code < 400 else "❌"

            logger.info(
                f"{status_emoji} {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.2f}s"
            )

        return response

    def get_client_ip(self, request):
        """Отримання IP клієнта."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware для обробки помилок 404 та 500.
    """

    def process_exception(self, request, exception):
        """
        Обробка необроблених виключень (500).
        """
        logger.error(
            f"💥 Internal Server Error: {str(exception)} | "
            f"Path: {request.path} | "
            f"Method: {request.method}",
            exc_info=True
        )

        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'Щось пішло не так. Спробуйте пізніше.',
            'status': 500
        }, status=500)

    def process_response(self, request, response):
        """
        Обробка 404 помилок.
        """
        if response.status_code == 404:
            logger.warning(
                f"🔍 404 Not Found: {request.path} | "
                f"Method: {request.method} | "
                f"User: {getattr(request.user, 'username', 'Anonymous')}"
            )

            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Not Found',
                    'message': f'Ендпоінт {request.path} не знайдено',
                    'status': 404
                }, status=404)

        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Додає security заголовки до відповіді.
    """

    def process_response(self, request, response):
        """Додає безпекові заголовки."""
        # Захист від XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'

        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline';"
            "frame-ancestors 'none';"  # Заборона embedding
        )

        # HSTS (для HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response


# class RateLimitMiddleware(MiddlewareMixin):
#     """
#     Простий rate limiter (для production використовуйте django-ratelimit).
#     """
#
#     def __init__(self, get_response):
#         super().__init__(get_response)
#         self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}
#         self.max_requests = 100  # Максимум запитів
#         self.time_window = 60  # За 60 секунд
#
#     def process_request(self, request):
#         """Перевіряє rate limit."""
#         ip = self.get_client_ip(request)
#         current_time = time.time()
#
#         # Очищуємо старі записи
#         if ip in self.requests:
#             self.requests[ip] = [
#                 t for t in self.requests[ip]
#                 if current_time - t < self.time_window
#             ]
#         else:
#             self.requests[ip] = []
#
#         # Перевіряємо ліміт
#         if len(self.requests[ip]) >= self.max_requests:
#             logger.warning(f"⚠️ Rate limit exceeded for IP: {ip}")
#             return JsonResponse({
#                 'error': 'Too Many Requests',
#                 'message': f'Перевищено ліміт запитів. Спробуйте через {self.time_window} секунд.',
#                 'status': 429
#             }, status=429)
#
#         # Додаємо новий запит
#         self.requests[ip].append(current_time)
#
#     def get_client_ip(self, request):
#         """Отримання IP клієнта."""
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             return x_forwarded_for.split(',')[0]
#         return request.META.get('REMOTE_ADDR')