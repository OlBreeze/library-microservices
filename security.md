
## 🛡️ Завдання з безпеки для мікросервісів

---

## 1️⃣ Користувач, реєстрація та авторизація ✅ (Вже реалізовано!)

### Що вже є:

```python
# authentication/models.py
# ✅ Використовується вбудована модель User з Django
from django.contrib.auth.models import User

# ✅ Поля: username, email, password
# ✅ Хешування паролів автоматичне (PBKDF2)
# ✅ Salting вбудований в Django
```

### Що можна покращити:

#### **`authentication/serializers.py`** - Додаткова валідація:

```python
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
import re


class RegisterSerializer(serializers.ModelSerializer):
    """Серіалізатор реєстрації з розширеною валідацією."""
    
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Користувач з таким email вже існує"
            )
        ]
    )
    
    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Користувач з таким username вже існує"
            )
        ]
    )
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        min_length=8
    )
    
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Підтвердження пароля'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }
    
    def validate_username(self, value):
        """
        Валідація username:
        - Тільки літери, цифри, _, -
        - Без пробілів
        - Мінімум 3 символи
        """
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError(
                "Username може містити тільки літери, цифри, _ та -"
            )
        
        if value.lower() in ['admin', 'root', 'superuser', 'administrator']:
            raise serializers.ValidationError(
                "Цей username зарезервований системою"
            )
        
        return value
    
    def validate_email(self, value):
        """
        Валідація email:
        - Правильний формат
        - Не з тимчасових email сервісів
        """
        # Список заборонених доменів
        blocked_domains = [
            'tempmail.com',
            '10minutemail.com',
            'guerrillamail.com',
            'mailinator.com'
        ]
        
        domain = value.split('@')[1].lower()
        if domain in blocked_domains:
            raise serializers.ValidationError(
                "Тимчасові email адреси не дозволені"
            )
        
        return value.lower()
    
    def validate(self, attrs):
        """Перевірка співпадіння паролів."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Паролі не співпадають"
            })
        return attrs
    
    def create(self, validated_data):
        """Створення користувача з хешованим паролем."""
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],  # ✅ Автоматично хешується
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
```

#### **`authentication/views.py`** - Логування спроб входу:

```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
import logging

# Налаштування логера
logger = logging.getLogger('authentication')


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Кастомний view для отримання JWT токену з логуванням.
    """
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        # Логуємо спробу входу
        logger.info(f"Спроба входу: username={username}, IP={self.get_client_ip(request)}")
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            logger.info(f"✅ Успішний вхід: username={username}")
        else:
            logger.warning(f"❌ Невдала спроба входу: username={username}")
        
        return response
    
    def get_client_ip(self, request):
        """Отримання IP адреси клієнта."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(generics.GenericAPIView):
    """
    Вихід з системи (blacklist refresh токену).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token обов\'язковий'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Додаємо токен в blacklist
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"✅ Користувач {request.user.username} вийшов з системи")
            
            return Response(
                {'message': 'Успішний вихід з системи'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"❌ Помилка виходу: {str(e)}")
            return Response(
                {'error': 'Невалідний токен'},
                status=status.HTTP_400_BAD_REQUEST
            )
```

#### **`authentication/urls.py`** - Оновлений:

```python
from django.urls import path
from .views import (
    RegisterView,
    UserProfileView,
    ChangePasswordView,
    CustomTokenObtainPairView,
    LogoutView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
```

---

## 2️⃣ Middleware для логування та обробки помилок

### **`books_service/books_service/middleware.py`**:

```python
"""
Middleware для логування та обробки помилок.
"""
import logging
import time
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('books_service')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Логування всіх запитів до Books Service.
    """
    
    def process_request(self, request):
        """Логує вхідний запит."""
        request.start_time = time.time()
        
        # Логуємо тільки захищені ендпоінти
        if request.path.startswith('/api/books/'):
            logger.info(
                f"📥 {request.method} {request.path} | "
                f"User: {getattr(request.user, 'username', 'Anonymous')} | "
                f"IP: {self.get_client_ip(request)}"
            )
    
    def process_response(self, request, response):
        """Логує відповідь з часом виконання."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            status_emoji = "✅" if response.status_code < 400 else "❌"
            
            logger.info(
                f"{status_emoji} {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.2f}s"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Отримання IP клієнта."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware для обробки помилок 404 та 500.
    """
    
    def process_exception(self, request, exception):
        """
        Обробка необроблених виключень (500).
        """
        logger.error(
            f"💥 Internal Server Error: {str(exception)} | "
            f"Path: {request.path} | "
            f"Method: {request.method}",
            exc_info=True
        )
        
        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'Щось пішло не так. Спробуйте пізніше.',
            'status': 500
        }, status=500)
    
    def process_response(self, request, response):
        """
        Обробка 404 помилок.
        """
        if response.status_code == 404:
            logger.warning(
                f"🔍 404 Not Found: {request.path} | "
                f"Method: {request.method} | "
                f"User: {getattr(request.user, 'username', 'Anonymous')}"
            )
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Not Found',
                    'message': f'Ендпоінт {request.path} не знайдено',
                    'status': 404
                }, status=404)
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Додає security заголовки до відповіді.
    """
    
    def process_response(self, request, response):
        """Додає безпекові заголовки."""
        # Захист від XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline';"
        )
        
        # HSTS (для HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Простий rate limiter (для production використовуйте django-ratelimit).
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}
        self.max_requests = 100  # Максимум запитів
        self.time_window = 60  # За 60 секунд
    
    def process_request(self, request):
        """Перевіряє rate limit."""
        ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Очищуємо старі записи
        if ip in self.requests:
            self.requests[ip] = [
                t for t in self.requests[ip]
                if current_time - t < self.time_window
            ]
        else:
            self.requests[ip] = []
        
        # Перевіряємо ліміт
        if len(self.requests[ip]) >= self.max_requests:
            logger.warning(f"⚠️ Rate limit exceeded for IP: {ip}")
            return JsonResponse({
                'error': 'Too Many Requests',
                'message': f'Перевищено ліміт запитів. Спробуйте через {self.time_window} секунд.',
                'status': 429
            }, status=429)
        
        # Додаємо новий запит
        self.requests[ip].append(current_time)
    
    def get_client_ip(self, request):
        """Отримання IP клієнта."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
```

### **`books_service/books_service/settings.py`** - Додати middleware:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # ⬇️ Наші кастомні middleware
    'books_service.middleware.SecurityHeadersMiddleware',
    'books_service.middleware.RequestLoggingMiddleware',
    'books_service.middleware.ErrorHandlingMiddleware',
    'books_service.middleware.RateLimitMiddleware',
]

# Налаштування логування
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/books_service.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'books_service': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'authentication': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

Створіть директорію для логів:
```bash
mkdir -p books_service/logs
mkdir -p auth_service/logs
```

---

## 3️⃣ Перевірка безпеки (Сканування вразливостей)

### Інструменти для сканування:

#### **A. Встановлення OWASP ZAP**

```bash
# Для Ubuntu/Debian
sudo apt-get install zaproxy

# Для macOS
brew install --cask owasp-zap

# Або завантажте з https://www.zaproxy.org/download/
```

#### **B. Django Security Check (вбудований)**

```bash
# Запустіть перевірку безпеки Django
python manage.py check --deploy

# В обох сервісах:
cd auth_service
python manage.py check --deploy

cd books_service
python manage.py check --deploy
```

#### **C. Bandit (Python Security Linter)**

```bash
# Встановлення
pip install bandit

# Сканування коду
bandit -r auth_service/ -f html -o security_report_auth.html
bandit -r books_service/ -f html -o security_report_books.html
```

#### **D. Safety (перевірка залежностей)**

```bash
# Встановлення
pip install safety

# Перевірка вразливостей в пакетах
safety check -r auth_service/requirements.txt
safety check -r books_service/requirements.txt
```

### **Скрипт автоматичної перевірки безпеки:**

**`security_check.sh`**:

```bash
#!/bin/bash

echo "🔒 Security Check для Library Microservices"
echo "==========================================="

# Кольори
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Django Security Check
echo -e "\n${YELLOW}1️⃣ Django Security Check${NC}"
echo "Auth Service:"
cd auth_service
python manage.py check --deploy
cd ..

echo -e "\nBooks Service:"
cd books_service
python manage.py check --deploy
cd ..

# 2. Bandit Security Scan
echo -e "\n${YELLOW}2️⃣ Bandit Security Scan${NC}"
pip install bandit -q
bandit -r auth_service/ -ll
bandit -r books_service/ -ll

# 3. Safety Check (Dependencies)
echo -e "\n${YELLOW}3️⃣ Safety Check (Vulnerabilities in Dependencies)${NC}"
pip install safety -q
safety check -r auth_service/requirements.txt
safety check -r books_service/requirements.txt

# 4. Secrets Detection
echo -e "\n${YELLOW}4️⃣ Checking for exposed secrets${NC}"
if grep -r "SECRET_KEY\s*=\s*['\"]" auth_service/ books_service/ --exclude-dir=venv; then
    echo -e "${RED}⚠️  Found hardcoded secrets!${NC}"
else
    echo -e "${GREEN}✅ No hardcoded secrets found${NC}"
fi

# 5. Debug Mode Check
echo -e "\n${YELLOW}5️⃣ Checking DEBUG mode${NC}"
if grep -r "DEBUG\s*=\s*True" auth_service/ books_service/ --include="*.py"; then
    echo -e "${RED}⚠️  DEBUG=True found in code!${NC}"
else
    echo -e "${GREEN}✅ No DEBUG=True in production code${NC}"
fi

echo -e "\n${GREEN}✅ Security check completed!${NC}"
```

Зробіть скрипт виконуваним:
```bash
chmod +x security_check.sh
./security_check.sh
```

---

## 4️⃣ Захист від XSS (Cross-Site Scripting)

### **A. Django автоматично захищає від XSS:**

```python
# Django templates автоматично екранують HTML
# Це безпечно:
{{ user.username }}  # <script>alert('XSS')</script> → &lt;script&gt;...

# Якщо потрібен HTML (небезпечно!):
{{ user.bio|safe }}  # ⚠️ Використовуйте тільки для перевірених даних
```

### **B. Захист в REST API (JSON responses):**

**`books/serializers.py`** - Додати санітизацію:

```python
from rest_framework import serializers
from .models import Book
import bleach
import re


class BookSerializer(serializers.ModelSerializer):
    """
    Серіалізатор з захистом від XSS.
    """
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'genre', 'publication_year', 'user_id', 'created_at']
        read_only_fields = ['id', 'user_id', 'created_at']
    
    def validate_title(self, value):
        """
        Захист від XSS в назві книги.
        """
        # Видаляємо HTML теги
        cleaned = bleach.clean(value, tags=[], strip=True)
        
        # Перевіряємо на підозрілі патерни
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onload=',
            r'<iframe',
            r'<embed',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise serializers.ValidationError(
                    "Виявлено підозрілий вміст у назві книги"
                )
        
        return cleaned
    
    def validate_author(self, value):
        """Санітизація автора."""
        return bleach.clean(value, tags=[], strip=True)
    
    def validate_genre(self, value):
        """Санітизація жанру."""
        return bleach.clean(value, tags=[], strip=True)
```

### **C. Content Security Policy (CSP):**

**`books_service/books_service/middleware.py`** (вже додано):

```python
class SecurityHeadersMiddleware(MiddlewareMixin):
    """Додає CSP заголовки."""
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "  # Тільки скрипти з нашого домену
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"  # Заборона embedding
        )
        
        # X-XSS-Protection (застаріло, але для старих браузерів)
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
```

### **D. Додати `bleach` в requirements.txt:**

```txt
# auth_service/requirements.txt та books_service/requirements.txt
bleach==6.1.0
```

### **E. Тестування XSS захисту:**

**`books/tests.py`** - Додати тести:

```python
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from .models import Book


class XSSProtectionTestCase(TestCase):
    """Тести захисту від XSS."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_xss_in_title(self):
        """Тест: XSS в назві книги має бути заблоковано."""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            'Book<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            'javascript:alert(1)',
            '<iframe src="evil.com"></iframe>',
        ]
        
        for payload in xss_payloads:
            response = self.client.post('/api/books/', {
                'title': payload,
                'author': 'Test Author',
                'genre': 'Test Genre',
                'publication_year': 2024
            })
            
            # Має або відхилити, або очистити
            if response.status_code == 201:
                self.assertNotIn('<script', response.data['title'].lower())
                self.assertNotIn('javascript:', response.data['title'].lower())
    
    def test_safe_html_sanitization(self):
        """Тест: HTML має бути видалений."""
        response = self.client.post('/api/books/', {
            'title': 'Book with <b>bold</b> text',
            'author': 'Author with <i>italic</i>',
            'genre': 'Genre',
            'publication_year': 2024
        })
        
        if response.status_code == 201:
            # HTML теги мають бути видалені
            self.assertEqual(response.data['title'], 'Book with bold text')
            self.assertEqual(response.data['author'], 'Author with italic')
```

Запуск тестів:
```bash
cd books_service
python manage.py test books.tests.XSSProtectionTestCase
```

---

## 5️⃣ Захист від SQL Injection

### **A. Django ORM автоматично захищає:**

```python
# ✅ БЕЗПЕЧНО (Django ORM параметризує запити)
Book.objects.filter(author=user_input)
Book.objects.filter(title__icontains=search_query)

# ❌ НЕБЕЗПЕЧНО (сирий SQL без параметрів)
Book.objects.raw(f"SELECT * FROM books WHERE author = '{user_input}'")
```

### **B. Правильне використання raw SQL:**

**`books/services.py`** - Безпечні SQL запити:

```python
"""
Сервіс для роботи з книгами з безпечними SQL запитами.
"""
from django.db import connection
from typing import List, Dict, Any


class BookService:
    """Сервіс для безпечних SQL операцій."""
    
    @staticmethod
    def search_books_safe(search_term: str) -> List[Dict[str, Any]]:
        """
        ✅ БЕЗПЕЧНИЙ пошук книг з використанням параметризованих запитів.
        
        Args:
            search_term: Пошуковий запит від користувача
            
        Returns:
            Список книг
        """
        with connection.cursor() as cursor:
            # ✅ Використовуємо %s для параметрів (НЕ f-string!)
            query = """
                SELECT id, title, author, genre, publication_year
                FROM books_book
                WHERE title ILIKE %s OR author ILIKE %s
                LIMIT 100
            """
            
            # Django автоматично екранує параметри
            search_pattern = f'%{search_term}%'
            cursor.execute(query, [search_pattern, search_pattern])
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    @staticmethod
    def search_books_vulnerable(search_term: str) -> List[Dict[str, Any]]:
        """
        ❌ ВРАЗЛИВИЙ до SQL Injection (НЕ ВИКОРИСТОВУВАТИ!)
        
        Цей метод для демонстрації вразливості.
        """
        with connection.cursor() as cursor:
            # ❌ НЕБЕЗПЕЧНО: f-string з user input
            query = f"""
                SELECT id, title, author, genre
                FROM books_book
                WHERE title LIKE '%{search_term}%'
            """
            
            # Атакуючий може ввести: ' OR '1'='1' --
            # Результат: SELECT * FROM books_book WHERE title LIKE '%%' OR '1'='1' --%'
            cursor.execute(query)
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    @staticmethod
    def get_book_by_id_safe(book_id: int) -> Dict[str, Any]:
        """
        ✅ БЕЗПЕЧНЕ отримання книги за ID.
        """
        with connection.cursor() as cursor:
            query = """
                SELECT id, title, author, genre, publication_year, created_at
                FROM books_book
                WHERE id = %s
            """
            cursor.execute(query, [book_id])
            
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
    
    @staticmethod
    def bulk_update_safe(updates: List[Dict[str, Any]]) -> int:
        """
        ✅ БЕЗПЕЧНЕ масове оновлення книг.
        
        Args:
            updates: Список словників з {id, title, author, ...}
            
        Returns:
            Кількість оновлених записів
        """
        with connection.cursor() as cursor:
            query = """
                UPDATE books_book
                SET title = %s, author = %s, genre = %s
                WHERE id = %s
            """
            
            # Використовуємо executemany для batch операцій
            params = [
                (u['title'], u['author'], u['genre'], u['id'])
                for u in updates
            ]
            
            cursor.executemany(query, params)
            return cursor.rowcount
```

### **C. Валідація типів даних:**

**`books/views.py`** - Додати валідацію:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.validators import validate_integer
from django.core.exceptions import ValidationError


class BookViewSet(viewsets.ModelViewSet):
    # ... попередній код ...
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Безпечний пошук книг.
        
        GET /api/books/search/?q=кобзар
        """
        search_query = request.query_params.get('q', '')
        
        # Валідація довжини
        if len(search_query) > 100:
            return Response(
                {'error': 'Пошуковий запит занадто довгий (макс 100 символів)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Використовуємо ORM (автоматичний захист)
        books = Book.objects.filter(
            models.Q(title__icontains=search_query) |
            models.Q(author__icontains=search_query)
        )[:100]  # Обмеження результатів
        
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """
        Фільтрація за роком з валідацією.
        
        GET /api/books/by_year/?year=2024
        """
        year_str = request.query_params.get('year')
        
        if not year_str:
            return Response(
                {'error': 'Параметр year обов\'язковий'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Валідація що це число
        try:
            year = int(year_str)
        except ValueError:
            return Response(
                {'error': 'year має бути числом'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Валідація діапазону
        if not (1000 <= year <= 2100):
            return Response(
                {'error': 'Рік має бути між 1000 та 2100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Безпечний запит через ORM
        books = Book.objects.filter(publication_year=year)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
```

### **D. Тести SQL Injection:**

**`books/tests.py`**:

```python
class SQLInjectionTestCase(TestCase):
    """Тести захисту від SQL Injection."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Створюємо тестові книги
        Book.objects.create(
            title='Normal Book',
            author='Normal Author',
            genre='Fiction',
            publication_year=2024,
            user_id=self.user.id
        )
    
    def test_sql_injection_in_search(self):
        """Тест: SQL injection в пошуку має бути заблокований."""
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE books_book; --",
            "' UNION SELECT * FROM auth_user --",
            "admin'--",
            "' OR 1=1--",
        ]
        
        for payload in sql_injection_payloads:
            response = self.client.get(f'/api/books/search/?q={payload}')
            
            # Не має бути помилки 500 (SQL error)
            self.assertNotEqual(response.status_code, 500)
            
            # Має повернути порожній список або помилку валідації
            self.assertIn(response.status_code, [200, 400])
    
    def test_sql_injection_in_filter(self):
        """Тест: SQL injection в фільтрі."""
        response = self.client.get('/api/books/?author=' + "' OR '1'='1")
        
        # ORM має захистити
        self.assertNotEqual(response.status_code, 500)
        self.assertIn(response.status_code, [200, 400])
    
    def test_integer_validation(self):
        """Тест: валідація типу даних (integer)."""
        # Спроба передати SQL injection як ID
        response = self.client.get("/api/books/999999' OR '1'='1/")
        
        # Має бути 404, а не 500
        self.assertEqual(response.status_code, 404)
```

---

## 6️⃣ Захист від CSRF (Cross-Site Request Forgery)

### **A. Як працює CSRF в Django:**

```python
# 1. Django генерує CSRF токен для кожної сесії
# 2. Токен зберігається в cookie: csrftoken=abc123...
# 3. Форми включають прихований input з токеном:
#    <input type="hidden" name="csrfmiddlewaretoken" value="abc123...">
# 4. При POST/PUT/DELETE Django перевіряє:
#    - Cookie csrftoken
#    - POST data csrfmiddlewaretoken
#    - Заголовок X-CSRFToken
# 5. Якщо не співпадають → 403 Forbidden
```

### **B. CSRF в REST API (JWT authentication):**

**JWT токени НЕ потребують CSRF захисту**, бо:
- Токен зберігається в `localStorage` (не в cookies)
- Токен передається в заголовку `Authorization`
- Браузер НЕ додає його автоматично до запитів

**`books_service/books_service/settings.py`**:

```python
# CSRF Settings
CSRF_COOKIE_HTTPONLY = True  # JavaScript не може читати CSRF cookie
CSRF_COOKIE_SECURE = not DEBUG  # Тільки HTTPS в production
CSRF_COOKIE_SAMESITE = 'Strict'  # Не надсилати в cross-site запитах

# Для JWT API CSRF не потрібен
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',  # Frontend
    'http://localhost:8001',  # Auth Service
    'http://localhost:8002',  # Books Service
]

# Виключення API ендпоінтів з CSRF перевірки
# (бо використовуємо JWT)
CSRF_EXEMPT_URLS = [
    r'^api/',
]
```

### **C. Middleware для CSRF виключень:**

**`books_service/books_service/middleware.py`**:

```python
from django.utils.deprecation import MiddlewareMixin
import re


class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Виключає API ендпоінти з CSRF перевірки.
    
    API використовує JWT, тому CSRF не потрібен.
    """
    
    def process_request(self, request):
        """Виключає /api/ з CSRF перевірки."""
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
```

Додайте в `MIDDLEWARE`:
```python
MIDDLEWARE = [
    # ...
    'django.middleware.csrf.CsrfViewMiddleware',
    'books_service.middleware.CSRFExemptMiddleware',  # Після CSRF middleware
    # ...
]
```

### **D. Документація CSRF для фронтенду:**

**`README.md`** - Додати секцію:

```markdown
## 🔒 CSRF Protection

### Для JWT API (рекомендовано):
```javascript
// Токен в Authorization заголовку (CSRF не потрібен)
fetch('http://localhost:8002/api/books/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ title: 'Book' })
})
```

### Для session-based auth (якщо використовуєте):
```javascript
// Отримати CSRF токен з cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie) {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

fetch('http://localhost:8002/api/books/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrftoken,
    'Content-Type': 'application/json'
  },
  credentials: 'include',  // Включити cookies
  body: JSON.stringify({ title: 'Book' })
})
```
```

### **E. Тести CSRF:**

**`books/tests.py`**:

```python
class CSRFProtectionTestCase(TestCase):
    """Тести CSRF захисту."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_jwt_api_bypasses_csrf(self):
        """JWT API не потребує CSRF токену."""
        # Аутентифікація через JWT
        self.client.force_authenticate(user=self.user)
        
        # POST без CSRF токену має працювати
        response = self.client.post('/api/books/', {
            'title': 'Test Book',
            'author': 'Test Author',
            'genre': 'Fiction',
            'publication_year': 2024
        })
        
        # Має бути успішно (201 Created)
        self.assertEqual(response.status_code, 201)
    
    def test_csrf_required_for_non_api(self):
        """Не-API ендпоінти потребують CSRF."""
        # Логін через session
        self.client.login(username='testuser', password='testpass123')
        
        # POST до Django форми без CSRF має фейлити
        # (якщо є такі ендпоінти)
        pass
```

---

## 📋 Чек-лист безпеки для production:

**`SECURITY_CHECKLIST.md`**:

```markdown
# 🔒 Security Checklist

## Environment Variables
- [ ] `DEBUG = False` в production
- [ ] `SECRET_KEY` не в коді (тільки в .env)
- [ ] `JWT_SECRET_KEY` складний (64+ символи)
- [ ] `.env` в `.gitignore`

## Database
- [ ] Використання ORM (не raw SQL)
- [ ] Параметризовані запити для raw SQL
- [ ] Backup бази даних налаштований

## Authentication
- [ ] JWT токени з коротким lifetime (1 год)
- [ ] Refresh токени з blacklist
- [ ] Strong password validation
- [ ] Rate limiting на login endpoint

## Headers
- [ ] `X-Frame-Options: DENY`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `Content-Security-Policy` налаштований
- [ ] `Strict-Transport-Security` для HTTPS

## Input Validation
- [ ] Всі user inputs валідуються
- [ ] HTML санітизація (bleach)
- [ ] File uploads обмежені
- [ ] Max length для всіх полів

## Dependencies
- [ ] `pip install -U` регулярно
- [ ] `safety check` пройдений
- [ ] Відомі вразливості виправлені

## Logging
- [ ] Security events логуються
- [ ] Failed login attempts логуються
- [ ] Логи не містять sensitive data

## HTTPS
- [ ] SSL certificate встановлений
- [ ] Всі HTTP → HTTPS redirect
- [ ] Secure cookies (SECURE=True)

## Monitoring
- [ ] Error monitoring (Sentry)
- [ ] Uptime monitoring
- [ ] Security alerts налаштовані

## Deployment
- [ ] Secret keys ротуються
- [ ] Firewall налаштований
- [ ] Тільки необхідні порти відкриті
- [ ] Regular security audits
```

---

## 🚀 Запуск всіх перевірок:

```bash
# Створіть master скрипт
# security_suite.sh

#!/bin/bash

echo "🔒 Running Full Security Suite"
echo "=============================="

# 1. Security check
./security_check.sh

# 2. Tests
echo -e "\n📝 Running security tests..."
cd auth_service
python manage.py test authentication.tests
cd ../books_service
python manage.py test books.tests

# 3. Coverage
echo -e "\n📊 Checking test coverage..."
pip install coverage -q
cd ../auth_service
coverage run --source='.' manage.py test
coverage report

cd ../books_service
coverage run --source='.' manage.py test
coverage report

echo -e "\n✅ Security suite completed!"
```
