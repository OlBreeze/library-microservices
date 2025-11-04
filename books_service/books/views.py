from django.conf import settings
from django.contrib.sites import requests
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Book
from .serializers import BookSerializer, BookListSerializer
from .filters import BookFilter
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управління книгами.

    Надає наступні ендпоінти:
    - GET /api/books/ - список всіх книг (з пагінацією, фільтрацією та пошуком)
    - POST /api/books/ - створення нової книги
    - GET /api/books/{id}/ - деталі окремої книги
    - PUT /api/books/{id}/ - повне оновлення книги
    - PATCH /api/books/{id}/ - часткове оновлення книги
    - DELETE /api/books/{id}/ - видалення книги (тільки для адміністраторів)
    - GET /api/books/my_books/ - книги поточного користувача
    - GET /api/books/statistics/ - статистика по книгах

    Фільтрація:
    - author: фільтрація за автором
    - genre: фільтрація за жанром
    - publication_year: фільтрація за роком видання
    - year_from: книги від вказаного року
    - year_to: книги до вказаного року

    Пошук:
    - search: пошук за назвою або автором

    Сортування:
    - ordering: сортування за полями (title, author, publication_year, created_at)
      Для зворотного сортування використовуйте '-' перед полем (наприклад, -publication_year)
    """
    queryset = Book.objects.select_related('user').all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookFilter
    search_fields = ['title', 'author']
    ordering_fields = ['title', 'author', 'publication_year', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Повертає відповідний серіалізатор в залежності від дії.

        Returns:
            BookListSerializer для списку книг
            BookSerializer для деталей та операцій створення/оновлення
        """
        if self.action == 'list':
            return BookListSerializer
        return BookSerializer

    def perform_create(self, serializer):
        """
        Зберігає нову книгу з поточним користувачем як власником.

        Args:
            serializer: Серіалізатор з валідованими даними
        """
        """
                Зберігає книгу з user_id з JWT токену.

                JWT токен містить: {"user_id": 3, "username": "gala", ...}
                """
        # Дістаємо user_id з токену
        # id = self.request.user.id
        id = getattr(self.request.user, 'id', None)
        # Зберігаємо книгу з user_id
        serializer.save(user_id=id)

    @swagger_auto_schema(
        operation_description="Отримати список книг поточного користувача",
        responses={200: BookSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def my_books(self, request):
        """
        Повертає список книг, створених поточним користувачем.

        Args:
            request: HTTP запит

        Returns:
            Response зі списком книг користувача
        """
        user_id = request.user.id
        books = self.queryset.filter(user_id=user_id)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def with_user_info(self, request, pk=None):
        """
        Отримати книгу з повною інформацією про користувача.

        Робить HTTP запит до Auth Service для отримання даних користувача.
        """
        book = self.get_object()

        # Запит до Auth Service
        try:
            auth_response = requests.get(
                f"{settings.AUTH_SERVICE_URL}/api/auth/users/{book.user_id}/",
                headers={'Authorization': request.headers.get('Authorization')},
                timeout=5
            )

            if auth_response.status_code == 200:
                user_data = auth_response.json()
            else:
                user_data = {'id': book.user_id, 'error': 'User not found'}
        except requests.RequestException as e:
            user_data = {'id': book.user_id, 'error': str(e)}

        # Об'єднуємо дані
        book_data = self.get_serializer(book).data
        book_data['user_info'] = user_data

        return Response(book_data)

    @swagger_auto_schema(
        operation_description="Отримати статистику по книгах",
        responses={
            200: openapi.Response(
                description="Статистика",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_books': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_authors': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_genres': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'my_books_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Повертає статистику по всіх книгах.

        Args:
            request: HTTP запит

        Returns:
            Response зі статистикою
        """
        total_books = self.queryset.count()
        total_authors = self.queryset.values('author').distinct().count()
        total_genres = self.queryset.values('genre').distinct().count()
        my_books = self.queryset.filter(user_id=request.user.id).count()

        return Response({
            'total_books': total_books,
            'total_authors': total_authors,
            'total_genres': total_genres,
            'my_books_count': my_books,
        })
