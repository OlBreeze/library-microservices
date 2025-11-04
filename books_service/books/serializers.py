from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для моделі Book.

    Автоматично визначає поле user як поточного користувача.
    Включає дані про користувача, який створив запис (read-only).
    """
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'genre',
            'publication_year',
            'user',
            'user_id',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_id', 'created_at']

    def validate_publication_year(self, value: int) -> int:
        """
        Валідація року видання.

        Args:
            value: Рік видання

        Returns:
            Валідований рік видання

        Raises:
            ValidationError: Якщо рік видання більший за поточний рік
        """
        from datetime import datetime
        current_year = datetime.now().year

        if value > current_year:
            raise serializers.ValidationError(
                f"Рік видання не може бути більшим за поточний рік ({current_year})"
            )

        if value < 1000:
            raise serializers.ValidationError(
                "Рік видання повинен бути не менше 1000"
            )

        return value

    def validate_title(self, value: str) -> str:
        """
        Валідація назви книги.

        Args:
            value: Назва книги

        Returns:
            Валідована назва книги

        Raises:
            ValidationError: Якщо назва порожня або містить тільки пробіли
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Назва книги не може бути порожньою")
        return value.strip()


class BookListSerializer(serializers.ModelSerializer):
    """
    Спрощений серіалізатор для списку книг.
    Включає мінімальну інформацію для оптимізації продуктивності.
    """
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'genre', 'publication_year', 'user']

