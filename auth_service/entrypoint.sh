#!/bin/bash

# Виходимо при помилці
set -e

echo "🔐 Starting Auth Service..."

# Чекаємо на доступність бази даних (якщо PostgreSQL)
# if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
#     echo "Waiting for postgres..."
#     while ! nc -z $DB_HOST $DB_PORT; do
#       sleep 0.1
#     done
#     echo "PostgreSQL started"
# fi

# Виконуємо міграції
echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Збираємо статичні файли
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Створюємо суперкористувача (опціонально)
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
END

echo "✅ Auth Service is ready!"

# Запускаємо сервер
exec python manage.py runserver 0.0.0.0:8000