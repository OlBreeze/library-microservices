from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer, UserProfileSerializer
import logging


class RegisterView(generics.CreateAPIView):
    """
    API ендпоінт для реєстрації нових користувачів.

    POST /api/auth/register/

    Не вимагає аутентифікації. Приймає дані нового користувача та створює акаунт.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        operation_description="Реєстрація нового користувача",
        responses={
            201: openapi.Response(
                description="Користувач успішно зареєстрований",
                schema=UserSerializer
            ),
            400: "Помилка валідації"
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Створює нового користувача.

        Args:
            request: HTTP запит з даними користувача

        Returns:
            Response з даними створеного користувача
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'message': 'Користувач успішно зареєстрований'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API ендпоінт для перегляду та оновлення профілю користувача.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    # --- ЗМІНА ТУТ: Перевизначаємо perform_update ---
    def perform_update(self, serializer):
        # 1. Оновлюємо основну модель User
        user = serializer.save()

        # 2. Оновлюємо модель UserProfile, якщо дані присутні в запиті
        if 'profile' in self.request.data:
            profile_data = self.request.data.pop('profile')

            # Використовуємо UserProfileSerializer для валідації та оновлення
            # Об'єкт профілю отримуємо через related_name 'profile'
            profile_instance = user.profile
            profile_serializer = UserProfileSerializer(
                profile_instance,
                data=profile_data,
                partial=True  # Дозволяємо часткове оновлення (PATCH)
            )

            # Перевірка валідності даних профілю
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

    # --- Інші методи (get, put, patch) залишаються без змін ---
    @swagger_auto_schema(
        operation_description="Отримати профіль поточного користувача"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Оновити профіль користувача"
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частково оновити профіль користувача"
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """
    API ендпоінт для зміни пароля користувача.

    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Зміна пароля користувача",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Пароль успішно змінено",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Невірний старий пароль або помилка валідації"
        }
    )
    def post(self, request):
        """
        Змінює пароль користувача.

        Args:
            request: HTTP запит зі старим та новим паролем

        Returns:
            Response з повідомленням про успішну зміну або помилку
        """
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user

            # Перевірка старого пароля
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({
                    'old_password': ['Невірний пароль']
                }, status=status.HTTP_400_BAD_REQUEST)

            # Встановлення нового пароля
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({
                'message': 'Пароль успішно змінено'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====== НОВЫЙ ENDPOINT ДЛЯ BOOKS SERVICE ======
class UserDetailView(APIView):
    """
    API ендпоінт для отримання інформації про користувача за ID.
    Використовується мікросервісом книг для перевірки користувача.

    GET /api/auth/users/{id}/

    Вимагає JWT токен в заголовку Authorization.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Отримати інформацію про користувача за ID",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="ID користувача",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Інформація про користувача",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: "Користувач не знайдений"
        }
    )
    def get(self, request, user_id):
        """
        Повертає інформацію про користувача.

        Args:
            request: HTTP запит з токеном
            user_id: ID користувача

        Returns:
            Response з даними користувача
        """
        user = get_object_or_404(User, id=user_id)

        # Повертаємо тільки необхідні дані
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }, status=status.HTTP_200_OK)


# Налаштування логера!!!
# ---------------------------------------------------------------
logger = logging.getLogger('authentication')


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Кастомний view для отримання JWT токену з логуванням.
    """

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')

        # Логуємо спробу входу
        logger.info(f"Спроба входу: username={username}, IP={self.get_client_ip(request)}")

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            logger.info(f"✅ Успішний вхід: username={username}")
        else:
            logger.warning(f"❌ Невдала спроба входу: username={username}")

        return response

    def get_client_ip(self, request):
        """Отримання IP адреси клієнта."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(generics.GenericAPIView):
    """
    Вихід з системи (blacklist refresh токену).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token обов\'язковий'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Додаємо токен в blacklist
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"✅ Користувач {request.user.username} вийшов з системи")

            return Response(
                {'message': 'Успішний вихід з системи'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"❌ Помилка виходу: {str(e)}")
            return Response(
                {'error': 'Невалідний токен'},
                status=status.HTTP_400_BAD_REQUEST
            )
