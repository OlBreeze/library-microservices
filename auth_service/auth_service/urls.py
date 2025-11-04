"""
URL configuration for auth_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Налаштування Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Library API (Created by Olga and Swagger)",
        default_version='v1',
        description="""
        REST API для управління пользователями.

        ## Основні можливості:
        - JWT аутентифікація
        - Реєстрація та управління профілем користувача

        ## Аутентифікація:
        1. Отримайте токен через /api/auth/token/
        2. Використовуйте токен в заголовку: `Authorization: Bearer <token>`
        """,
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="contact@library.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('authentication.urls')),

    # JWT Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
