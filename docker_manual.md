# Docker-інфраструктура для обох мікросервісів.

## 📁 Структура проєкту:

```
library-microservices/
├── .env                        # Спільні змінні оточення
├── .env.example                # Приклад для GitHub
├── .gitignore
├── docker-compose.yml          # Оркестрація сервісів
├── README.md
│
├── auth_service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── entrypoint.sh          # Скрипт запуску
│   ├── auth_service/
│   │   ├── settings.py
│   │   └── urls.py
│   └── authentication/
│       ├── models.py
│       └── views.py
│
└── books_service/
    ├── Dockerfile
    ├── requirements.txt
    ├── manage.py
    ├── entrypoint.sh
    ├── books_service/
    │   ├── settings.py
    │   └── urls.py
    └── books/
        ├── models.py
        └── views.py
```

---

## 🔧 Файли конфігурації:

### **`.env`** (в корені):

```bash
# JWT Configuration
JWT_SECRET_KEY=super-secret-production-key-change-me-12345
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Django
DEBUG=True
DJANGO_SECRET_KEY=django-secret-key-change-me-in-production

# Database (для production можна використати PostgreSQL)
DB_ENGINE=django.db.backends.sqlite3

# URLs
AUTH_SERVICE_URL=http://auth_service:8000
BOOKS_SERVICE_URL=http://books_service:8000
```

### **`.env.example`** (для GitHub):

```bash
# Copy this file to .env and fill in your values

JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

DEBUG=True
DJANGO_SECRET_KEY=your-django-secret-key-here

DB_ENGINE=django.db.backends.sqlite3

AUTH_SERVICE_URL=http://auth_service:8000
BOOKS_SERVICE_URL=http://books_service:8000
```

### **`.gitignore`**:

```gitignore
# Environment
.env
*.env
!.env.example

# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class
*.so

# Django
*.log
db.sqlite3
db_*.sqlite3
*/migrations/*
!*/migrations/__init__.py
media/
staticfiles/

# Virtual environments
venv/
env/
.venv/

# Docker
*.pid
*.seed
*.pid.lock

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
```

---

## 🐳 Auth Service Docker:

### **`auth_service/Dockerfile`**:

```dockerfile
# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо змінні оточення
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements та встановлюємо Python залежності
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копіюємо код проєкту
COPY . /app/

# Копіюємо та надаємо права на entrypoint скрипт
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Відкриваємо порт
EXPOSE 8000

# Запускаємо entrypoint скрипт
ENTRYPOINT ["/app/entrypoint.sh"]
```

### **`auth_service/entrypoint.sh`**:

```bash
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
```

### **`auth_service/requirements.txt`**:

```txt
Django==4.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
drf-yasg==1.21.7
python-decouple==3.8
django-cors-headers==4.3.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

### **`auth_service/auth_service/settings.py`** (оновлений):

```python
import os
from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
    
    # Local
    'authentication',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'auth_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'auth_service.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': BASE_DIR / 'db_users.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'uk-ua'
TIME_ZONE = 'Europe/Kiev'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        hours=config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=1, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': config('JWT_ALGORITHM', default='HS256'),
    'SIGNING_KEY': config('JWT_SECRET_KEY', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True  # Для розробки
# Для production:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://localhost:8002",
# ]

# Swagger
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
}
```

---

## 🐳 Books Service Docker:

### **`books_service/Dockerfile`**:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
```

### **`books_service/entrypoint.sh`**:

```bash
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
```

### **`books_service/requirements.txt`**:

```txt
Django==4.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
django-filter==23.3
drf-yasg==1.21.7
python-decouple==3.8
django-cors-headers==4.3.0
requests==2.31.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

### **`books_service/books_service/settings.py`** (додайте CORS):

```python
# ... попередні налаштування ...

INSTALLED_APPS = [
    # ...
    'corsheaders',  # Додайте
    # ...
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Додайте
    # ...
]

# CORS
CORS_ALLOW_ALL_ORIGINS = True  # Для розробки
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8001",  # Auth Service
    "http://auth_service:8000",
]

# Auth Service URL
AUTH_SERVICE_URL = config('AUTH_SERVICE_URL', default='http://localhost:8001')
```

---

## 🐳 Docker Compose:

### **`docker-compose.yml`**:

```yaml
version: '3.8'

services:
  # ============================================
  # Auth Service (Port 8001)
  # ============================================
  auth_service:
    build:
      context: ./auth_service
      dockerfile: Dockerfile
    container_name: library_auth_service
    ports:
      - "8001:8000"
    environment:
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=${JWT_ALGORITHM}
      - JWT_ACCESS_TOKEN_LIFETIME_HOURS=${JWT_ACCESS_TOKEN_LIFETIME_HOURS}
      - JWT_REFRESH_TOKEN_LIFETIME_DAYS=${JWT_REFRESH_TOKEN_LIFETIME_DAYS}
      - DEBUG=${DEBUG}
      - DB_ENGINE=${DB_ENGINE}
    volumes:
      - ./auth_service:/app
      - auth_static:/app/staticfiles
      - auth_db:/app/db
    networks:
      - library_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/admin/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ============================================
  # Books Service (Port 8002)
  # ============================================
  books_service:
    build:
      context: ./books_service
      dockerfile: Dockerfile
    container_name: library_books_service
    ports:
      - "8002:8000"
    environment:
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=${JWT_ALGORITHM}
      - DEBUG=${DEBUG}
      - DB_ENGINE=${DB_ENGINE}
      - AUTH_SERVICE_URL=${AUTH_SERVICE_URL}
    volumes:
      - ./books_service:/app
      - books_static:/app/staticfiles
      - books_db:/app/db
    networks:
      - library_network
    depends_on:
      auth_service:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/admin/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ============================================
  # Nginx (Reverse Proxy) - опціонально
  # ============================================
  nginx:
    image: nginx:alpine
    container_name: library_nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - auth_static:/static/auth:ro
      - books_static:/static/books:ro
    networks:
      - library_network
    depends_on:
      - auth_service
      - books_service
    restart: unless-stopped

# ============================================
# Networks
# ============================================
networks:
  library_network:
    driver: bridge

# ============================================
# Volumes (збереження даних)
# ============================================
volumes:
  auth_static:
  books_static:
  auth_db:
  books_db:
```

---

## 🌐 Nginx Configuration (опціонально):

### **`nginx.conf`**:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream auth_service {
        server auth_service:8000;
    }

    upstream books_service {
        server books_service:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Auth Service
        location /api/auth/ {
            proxy_pass http://auth_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /auth-admin/ {
            proxy_pass http://auth_service/admin/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Books Service
        location /api/books/ {
            proxy_pass http://books_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /books-admin/ {
            proxy_pass http://books_service/admin/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Static files
        location /static/auth/ {
            alias /static/auth/;
        }

        location /static/books/ {
            alias /static/books/;
        }

        # Swagger Docs
        location /docs/ {
            proxy_pass http://books_service/docs/;
            proxy_set_header Host $host;
        }
    }
}
```

---

## 🚀 Запуск проєкту:

### **Скрипт `start.sh`**:

```bash
#!/bin/bash

echo "🚀 Starting Library Microservices..."

# Перевірка .env файлу
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your settings"
    exit 1
fi

# Зупиняємо старі контейнери
echo "🛑 Stopping old containers..."
docker-compose down

# Будуємо образи
echo "🔨 Building Docker images..."
docker-compose build

# Запускаємо сервіси
echo "▶️  Starting services..."
docker-compose up -d

# Чекаємо на запуск
echo "⏳ Waiting for services to start..."
sleep 10

# Перевіряємо статус
echo "📊 Services status:"
docker-compose ps

echo ""
echo "✅ Services are running!"
echo ""
echo "🔐 Auth Service:"
echo "   - API: http://localhost:8001/api/auth/"
echo "   - Admin: http://localhost:8001/admin/"
echo "   - Docs: http://localhost:8001/docs/"
echo ""
echo "📚 Books Service:"
echo "   - API: http://localhost:8002/api/books/"
echo "   - Admin: http://localhost:8002/admin/"
echo "   - Docs: http://localhost:8002/docs/"
echo ""
echo "🌐 Nginx (if enabled):"
echo "   - http://localhost/api/auth/"
echo "   - http://localhost/api/books/"
echo ""
echo "👤 Default credentials: admin / admin123"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
```

Зробіть скрипт виконуваним:
```bash
chmod +x start.sh
```

---

## 📝 Корисні команди:

```bash
# Запуск всіх сервісів
docker-compose up -d

# Перегляд логів
docker-compose logs -f

# Перегляд логів конкретного сервісу
docker-compose logs -f auth_service
docker-compose logs -f books_service

# Зупинка
docker-compose down

# Зупинка з видаленням volumes (БД буде очищена!)
docker-compose down -v

# Перезапуск конкретного сервісу
docker-compose restart auth_service

# Виконання команди в контейнері
docker-compose exec auth_service python manage.py createsuperuser
docker-compose exec books_service python manage.py migrate

# Перегляд запущених контейнерів
docker-compose ps

# Перебудова образів
docker-compose build --no-cache

# Масштабування (запуск кількох інстансів)
docker-compose up -d --scale books_service=3
```

---

## 🧪 Тестування:

```bash
# 1. Реєстрація через Auth Service
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
  }'

# 2. Отримання токену
TOKEN=$(curl -X POST http://localhost:8001/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}' \
  | jq -r '.access')

# 3. Створення книги через Books Service
curl -X POST http://localhost:8002/api/books/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Кобзар",
    "author": "Тарас Шевченко",
    "genre": "Поезія",
    "publication_year": 1840
  }'

# 4. Отримання списку книг
curl -X GET http://localhost:8002/api/books/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 README.md для проєкту:

```markdown
# 📚 Library Microservices

REST API для управління бібліотекою книг з мікросервісною архітектурою.

## 🏗️ Архітектура

- **Auth Service** (Port 8001) - Аутентифікація та управління користувачами
- **Books Service** (Port 8002) - Управління книгами
- **Nginx** (Port 80) - Reverse proxy (опціонально)

## 🚀 Швидкий старт

1. Клонуйте репозиторій:
```bash
git clone https://github.com/yourusername/library-microservices.git
cd library-microservices
```

2. Створіть `.env` файл:
```bash
cp .env.example .env
# Відредагуйте .env зі своїми налаштуваннями
```

3. Запустіть Docker Compose:
```bash
docker-compose up -d
```

4. Відкрийте браузер:
- Auth API: http://localhost:8001/docs/
- Books API: http://localhost:8002/docs/

## 📖 Документація

- [API Documentation](./docs/API.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Development Guide](./docs/DEVELOPMENT.md)

## 👤 Credentials

Default admin account:
- Username: `admin`
- Password: `admin123`

## 📝 License

MIT
```

---

## ✅ Що ви отримали:

1. ✅ Повна Docker-інфраструктура
2. ✅ Автоматичні міграції при запуску
3. ✅ Healthchecks для сервісів
4. ✅ Збереження даних через volumes
5. ✅ CORS налаштований
6. ✅ Nginx reverse proxy
7. ✅ Скрипт автоматичного запуску
8. ✅ Production-ready конфігурація

Тепер просто запустіть:
```bash
./start.sh
```
