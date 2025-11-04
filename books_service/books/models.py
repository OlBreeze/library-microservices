from django.contrib.auth.models import User
from django.db import models

class Book(models.Model):
    """
        Модель для представлення книги в бібліотеці.

        Attributes:
            title (str): Назва книги (максимум 255 символів)
            author (str): Автор книги (максимум 255 символів)
            genre (str): Жанр книги (максимум 100 символів)
            publication_year (int): Рік видання (тільки позитивні числа)
            ⚠️ user_id - це просто число, НЕ ForeignKey!
                Зв'язок з користувачем через Auth Service API.
            created_at (datetime): Дата і час створення запису
        """

    title = models.CharField(
        max_length=255,
        verbose_name="Назва книги",
        help_text="Введіть назву книги"
    )
    author = models.CharField(
        max_length=255,
        verbose_name="Автор",
        help_text="Введіть ім'я автора книги"
    )
    genre = models.CharField(
        max_length=100,
        verbose_name="Жанр",
        help_text="Введіть жанр книги (наприклад, фантастика, детектив)"
    )
    publication_year = models.PositiveIntegerField(
        verbose_name="Рік видання",
        help_text="Введіть рік видання книги"
    )
    # ⚠️ Просто ID, не ForeignKey!
    user_id = models.IntegerField(
        verbose_name="ID користувача",
        help_text="ID користувача з Auth Service"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата створення"
    )

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['author']),
            models.Index(fields=['genre']),
        ]

    def __str__(self) -> str:
        """Повертає рядкове представлення книги."""
        return f"{self.title} ({self.author}, {self.publication_year})"
