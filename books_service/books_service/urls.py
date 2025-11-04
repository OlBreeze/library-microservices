from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Налаштування Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Library API (Created by Olga and Swagger)",
        default_version='v1',
        description="""
        REST API для управління бібліотекою книг.
        
        ## Основні можливості:
        - CRUD операції для книг
        - Фільтрація за автором, жанром, роком видання
        - Пошук книг за назвою
        - Пагінація результатів
        - JWT аутентифікація
        - Реєстрація та управління профілем користувача
        
        ## Аутентифікація:
        1. Отримайте токен через /api/auth/token/
        2. Використовуйте токен в заголовку: `Authorization: Bearer <token>`
        
        ## Приклади фільтрації:
        - `/api/books/?author=Шевченко` - книги автора Шевченко
        - `/api/books/?genre=фантастика` - книги жанру фантастика
        - `/api/books/?year_from=2000&year_to=2020` - книги за період
        - `/api/books/?search=Кобзар` - пошук за назвою
        - `/api/books/?ordering=-publication_year` - сортування за роком (від нових)
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
    path('api/books/', include('books.urls')),
    # path('api/auth/', include('authentication.urls')),

    # # JWT Authentication
    # path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

