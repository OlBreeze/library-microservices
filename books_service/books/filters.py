from django_filters import rest_framework as filters
from .models import Book


class BookFilter(filters.FilterSet):
    """
    Фільтр для моделі Book.

    Filters:
        author: Фільтрація за автором (часткове співпадіння, регістронезалежне)
        genre: Фільтрація за жанром (часткове співпадіння, регістронезалежне)
        publication_year: Точна фільтрація за роком видання
        year_from: Фільтрація книг, виданих не раніше вказаного року
        year_to: Фільтрація книг, виданих не пізніше вказаного року
        title: Пошук за назвою (часткове співпадіння, регістронезалежне)
    """
    author = filters.CharFilter(
        field_name='author',
        lookup_expr='icontains',
        label='Автор'
    )
    genre = filters.CharFilter(
        field_name='genre',
        lookup_expr='icontains',
        label='Жанр'
    )
    publication_year = filters.NumberFilter(
        field_name='publication_year',
        label='Рік видання'
    )
    year_from = filters.NumberFilter(
        field_name='publication_year',
        lookup_expr='gte',
        label='Рік від'
    )
    year_to = filters.NumberFilter(
        field_name='publication_year',
        lookup_expr='lte',
        label='Рік до'
    )
    title = filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Назва'
    )

    class Meta:
        model = Book
        fields = ['author', 'genre', 'publication_year', 'title']