#!/bin/bash

set -e

echo "📚 Starting Books Service..."

# Чекаємо на Auth Service
echo "Waiting for Auth Service..."
while ! nc -z auth_service 8000; do
  sleep 1
done
echo "Auth Service is ready!"

# Міграції
echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Статичні файли
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Створюємо суперкористувача
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
END

echo "✅ Books Service is ready!"

exec python manage.py runserver 0.0.0.0:8000