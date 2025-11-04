"""
Кастомная аутентификация для микросервиса книг
Проверяет JWT токен и получает информацию о пользователе из Auth Service
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import requests


class StatelessJWTAuthentication(JWTAuthentication):
    """
    Аутентификация с проверкой пользователя через Auth Service
    """

    def authenticate(self, request):
        """
        Переопределяем authenticate чтобы сохранить сырой токен
        """
        # Получаем заголовок Authorization
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        # Валидируем токен
        validated_token = self.get_validated_token(raw_token)

        # Сохраняем сырой токен в request для использования в get_user
        request._raw_token = raw_token.decode('utf-8') if isinstance(raw_token, bytes) else raw_token

        # Получаем пользователя
        user = self.get_user(validated_token)

        return (user, validated_token)

    def get_user(self, validated_token):
        """
        Получает информацию о пользователе из Auth Service
        """
        user_id = validated_token.get("user_id")

        if not user_id:
            raise AuthenticationFailed("Token has no user_id")

        # Получаем токен из request (сохранили в authenticate)
        from rest_framework.request import Request
        import inspect

        # Ищем request в стеке вызовов
        raw_token = None
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            if 'request' in frame_locals:
                req = frame_locals['request']
                if hasattr(req, '_raw_token'):
                    raw_token = req._raw_token
                    break

        # Проверяем пользователя через Auth Service с токеном
        auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://localhost:8001')
        url = f"{auth_service_url}/api/auth/users/{user_id}/"

        headers = {}
        if raw_token:
            headers['Authorization'] = f'Bearer {raw_token}'

        try:
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                user_data = response.json()

                # Создаем объект-заглушку пользователя
                class StatelessUser:
                    """Временный объект пользователя без сохранения в БД"""

                    def __init__(self, data):
                        self.id = data["id"]
                        self.username = data["username"]
                        self.email = data.get("email", "")
                        self.is_authenticated = True
                        self.is_active = True
                        self.is_anonymous = False

                    def __str__(self):
                        return self.username

                return StatelessUser(user_data)

            elif response.status_code == 404:
                raise AuthenticationFailed("User not found in Auth Service")
            elif response.status_code == 401:
                raise AuthenticationFailed("Invalid or expired token")
            else:
                raise AuthenticationFailed(f"Auth Service error: {response.status_code}")

        except requests.Timeout:
            raise AuthenticationFailed("Auth Service timeout")
        except requests.ConnectionError:
            raise AuthenticationFailed("Cannot connect to Auth Service")
        except requests.RequestException as e:
            raise AuthenticationFailed(f"Auth Service request failed: {str(e)}")