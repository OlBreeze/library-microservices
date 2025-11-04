from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Админ-панель для управления книгами."""

    # Отображение полей в списке
    list_display = [
        'id',
        'title',
        'author',
        'genre',
        'publication_year',
        'user_id',
        'created_at'
    ]

    # Поля, которые можно редактировать прямо в списке
    list_editable = ['title', 'author', 'genre', 'publication_year']

    # Поиск
    search_fields = ['title', 'author', 'genre', 'user_id']

    # Фильтры
    list_filter = [
        'genre',
        'publication_year',
        'created_at'
    ]

    # Сортировка по умолчанию
    ordering = ['-created_at']

    # Количество элементов на странице
    list_per_page = 20

    # Поля только для чтения
    readonly_fields = ['created_at', 'id']

    # Организация полей в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'author', 'genre', 'publication_year')
        }),
        ('Метаданные', {
            'fields': ('user_id', 'created_at', 'id'),
            'classes': ('collapse',)
        }),
    )

    # Экспорт в CSV
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        """Экспорт выбранных книг в CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="books.csv"'

        # Добавляем BOM для правильного отображения кириллицы в Excel
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow(['ID', 'Название', 'Автор', 'Жанр', 'Год', 'ID Пользователя', 'Дата создания'])

        for book in queryset:
            writer.writerow([
                book.id,
                book.title,
                book.author,
                book.genre,
                book.publication_year,
                book.user_id,
                book.created_at.strftime('%Y-%m-%d %H:%M')
            ])

        self.message_user(request, f'Экспортировано {queryset.count()} книг')
        return response

    export_to_csv.short_description = 'Экспортировать выбранные книги в CSV'


# Настройка заголовков
admin.site.site_header = "📚 Администрирование библиотеки"
admin.site.site_title = "Библиотека - Админ"
admin.site.index_title = "Панель управления"