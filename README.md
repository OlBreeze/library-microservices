
При мікросервісній архітектурі кожен сервіс має **свою власну адмінку** на своєму порті.

## 🏗️ Приклад архітектури:

```
📦 Мікросервісна архітектура бібліотеки

┌─────────────────────────────────────────────────────────┐
│  🌐 API Gateway (опціонально)                           │
│  http://localhost:8000                                  │
│  - Маршрутизація запитів до сервісів                   │
└─────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           ▼                              ▼
┌──────────────────────┐      ┌──────────────────────┐
│  🔐 Auth Service     │      │  📚 Books Service    │
│  Port: 8001          │      │  Port: 8002          │
├──────────────────────┤      ├──────────────────────┤
│  Database: users.db  │      │  Database: books.db  │
│                      │      │                      │
│  Admin:              │      │  Admin:              │
│  localhost:8001/admin│      │  localhost:8002/admin│
│                      │      │                      │
│  API:                │      │  API:                │
│  /api/auth/register/ │      │  /api/books/         │
│  /api/auth/login/    │      │  /api/books/{id}/    │
│  /api/auth/profile/  │      │  /api/books/search/  │
└──────────────────────┘      └──────────────────────┘
```

## 📁 Структура проєкту:

```
library_microservices/
├── auth_service/              # Сервіс аутентифікації
│   ├── manage.py
│   ├── auth_service/
│   │   ├── settings.py        # PORT = 8001
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── authentication/        # App для аутентифікації
│   │   ├── models.py          # User (або custom User)
│   │   ├── admin.py           # ✅ Адмінка користувачів
│   │   ├── serializers.py
│   │   └── views.py
│   ├── db_users.sqlite3       # База користувачів
│   └── requirements.txt
│
└── books_service/             # Сервіс книг
    ├── manage.py
    ├── books_service/
    │   ├── settings.py        # PORT = 8002
    │   ├── urls.py
    │   └── wsgi.py
    ├── books/                 # App для книг
    │   ├── models.py          # Book (user_id як число)
    │   ├── admin.py           # ✅ Адмінка книг
    │   ├── serializers.py
    │   └── views.py
    ├── db_books.sqlite3       # База книг
    └── requirements.txt
```

## 🔧 Налаштування кожного сервісу:

### 1️⃣ Auth Service (Port 8001)

**`auth_service/settings.py`:**
```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_users.sqlite3',  # Окрема БД!
    }
}

# Allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'SIGNING_KEY': 'SHARED_SECRET_KEY_123',  # ⚠️ Однакова для обох сервісів!
}
```

**`authentication/admin.py`:**
```python
from django.contrib import admin
from django.contrib.auth.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'is_staff', 'date_joined']
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'is_active', 'date_joined']

admin.site.site_header = "🔐 Auth Service Admin"
admin.site.site_title = "Auth Admin"
```

**Запуск:**
```bash
cd auth_service
python manage.py runserver 8001
```

**Доступ:**
- API: `http://localhost:8001/api/auth/`
- Admin: `http://localhost:8001/admin/`

---

### 2️⃣ Books Service (Port 8002)

**`books_service/settings.py`:**
```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_books.sqlite3',  # Окрема БД!
    }
}

# JWT settings (для валідації токенів)
SIMPLE_JWT = {
    'SIGNING_KEY': 'SHARED_SECRET_KEY_123',  # ⚠️ Та ж сама!
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
```

**`books/models.py`:**
```python
from django.db import models

class Book(models.Model):
    """Модель книги без ForeignKey до User (мікросервісна архітектура)."""
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    publication_year = models.PositiveIntegerField()
    user_id = models.IntegerField()  # ⚠️ Просто ID, не ForeignKey!
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} (User ID: {self.user_id})"
```

**`books/admin.py`:**
```python
from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'genre', 'publication_year', 'user_id', 'created_at']
    list_editable = ['title', 'author', 'genre', 'publication_year']
    search_fields = ['title', 'author', 'genre']
    list_filter = ['genre', 'publication_year']
    
    def get_user_info(self, obj):
        """Показує інформацію про користувача через API Auth Service."""
        import requests
        try:
            response = requests.get(f'http://localhost:8001/api/users/{obj.user_id}/')
            if response.status_code == 200:
                user_data = response.json()
                return f"{user_data['username']} ({user_data['email']})"
        except:
            pass
        return f"User ID: {obj.user_id}"
    
    get_user_info.short_description = 'Користувач'

admin.site.site_header = "📚 Books Service Admin"
admin.site.site_title = "Books Admin"
```

**Запуск:**
```bash
cd books_service
python manage.py runserver 8002
```

**Доступ:**
- API: `http://localhost:8002/api/books/`
- Admin: `http://localhost:8002/admin/`

---

## 🔐 Як працює аутентифікація між сервісами:

```python
# 1. Користувач логінується в Auth Service
POST http://localhost:8001/api/auth/token/
{
  "username": "gala",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJh...",  # JWT токен
  "refresh": "eyJ0eXAiOiJKV1QiLC..."
}

# 2. Користувач використовує токен для Books Service
GET http://localhost:8002/api/books/
Headers: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJh...

# 3. Books Service валідує токен (використовуючи ту саму SECRET_KEY)
# 4. З токену дістається user_id
# 5. Книга зберігається з цим user_id
```

## 🎯 Переваги такої архітектури:

### ✅ Переваги:
1. **Незалежне масштабування** - Books Service може мати 10 інстансів, Auth - 2
2. **Різні технології** - Auth на Django, Books на FastAPI (якщо треба)
3. **Окремі команди** - команда auth не чіпає код books
4. **Безпека** - якщо зламають Books Service, користувачі залишаються в безпеці
5. **Легше деплоїти** - оновив тільки Books Service, Auth не чіпаєш

### ❌ Недоліки:
1. **Складніша архітектура** - треба керувати кількома сервісами
2. **Немає ForeignKey** - `user_id` це просто число, не можна `.user.username`
3. **Додаткові HTTP запити** - щоб отримати дані користувача
4. **Транзакції** - складно робити транзакції між сервісами
5. **Дві адмінки** - треба логінитись в кожну окремо

## 🚀 API Gateway (опціонально):

Можна додати **єдину точку входу**:

```python
# api_gateway/urls.py (Port 8000)
from django.urls import path, include
import requests

def proxy_auth(request, path):
    """Проксі для Auth Service."""
    url = f'http://localhost:8001/{path}'
    response = requests.request(
        method=request.method,
        url=url,
        headers=request.headers,
        data=request.body
    )
    return HttpResponse(response.content, status=response.status_code)

def proxy_books(request, path):
    """Проксі для Books Service."""
    url = f'http://localhost:8002/{path}'
    # ... аналогічно

urlpatterns = [
    path('api/auth/<path:path>', proxy_auth),
    path('api/books/<path:path>', proxy_books),
]
```

Тепер всі запити йдуть через `localhost:8000`, але він перенаправляє їх на відповідні сервіси.

## 📊 Підсумок:

| Параметр | Монолітна архітектура | Мікросервісна |
|----------|----------------------|---------------|
| **Адмінка** | Одна на `localhost:8000/admin/` | Дві: `8001/admin/` та `8002/admin/` |
| **База даних** | Одна спільна | Дві окремі |
| **ForeignKey** | ✅ Можна `book.user.username` | ❌ Тільки `book.user_id` |
| **Складність** | 🟢 Проста | 🔴 Складна |
| **Масштабування** | 🔴 Важко | 🟢 Легко |

# Django REST Framework JWT Authentication робить це автоматично:

# 1. Отримує токен з заголовка
token = request.headers.get('Authorization')  # "Bearer eyJhbGci..."

# 2. Видаляє "Bearer "
token = token.replace('Bearer ', '')  # "eyJhbGci..."

# 3. Декодує токен з SECRET_KEY

```python
try:
    payload = jwt.decode(
        token,
        settings.SIMPLE_JWT['SIGNING_KEY'],  # Той самий SECRET_KEY!
        algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
    )
    # payload = {"user_id": 3, "exp": 1762093974, ...}
    
    # 4. Дістає user_id
    user_id = payload['user_id']  # 3
    
    # 5. Створює "фейковий" User об'єкт
    request.user = AnonymousUser()
    request.user.id = user_id
    request.user.is_authenticated = True
    
except jwt.ExpiredSignatureError:
    return Response({"error": "Token expired"}, status=401)
except jwt.InvalidTokenError:
    return Response({"error": "Invalid token"}, status=401)


```
---

## 🚀 Запуск обох сервісів:

### **Варіант 1: Вручну (два термінали)**

```bash
# Термінал 1: Auth Service
cd auth_service
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001

# Термінал 2: Books Service
cd books_service
python manage.py migrate
python manage.py runserver 8002
```

### **Варіант 2: Docker Compose (рекомендую)**

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  auth_service:
    build: ./auth_service
    ports:
      - "8001:8000"
    environment:
      - JWT_SECRET_KEY=super-secret-key-123
      - JWT_ALGORITHM=HS256
    volumes:
      - ./auth_service:/app
    command: python manage.py runserver 0.0.0.0:8000

  books_service:
    build: ./books_service
    ports:
      - "8002:8000"
    environment:
      - JWT_SECRET_KEY=super-secret-key-123  # ⚠️ Той самий!
      - JWT_ALGORITHM=HS256
      - AUTH_SERVICE_URL=http://auth_service:8000
    volumes:
      - ./books_service:/app
    depends_on:
      - auth_service
    command: python manage.py runserver 0.0.0.0:8000
```

**Запуск:**
```bash
docker-compose up
```

---

## 🧪 Тестування:

```bash
# 1. Реєстрація
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

echo "Token: $TOKEN"

# 3. Створення книги (Books Service валідує токен!)
curl -X POST http://localhost:8002/api/books/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Кобзар",
    "author": "Тарас Шевченко",
    "genre": "Поезія",
    "publication_year": 1840
  }'

# 4. Отримання книги з інфо про користувача
curl -X GET http://localhost:8002/api/books/1/with_user_info/ \
  -H "Authorization: Bearer $TOKEN"
```

---
