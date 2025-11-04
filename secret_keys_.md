## 1️⃣ `DJANGO_SECRET_KEY`

### Що це?
Це **вбудований ключ Django** для криптографічних операцій фреймворку.

### Для чого використовується?
```python
# Django використовує його для:

# 1. CSRF токени (захист форм)
<input type="hidden" name="csrfmiddlewaretoken" value="...">

# 2. Підпис сесій
request.session['user_id'] = 123  # Підписується SECRET_KEY

# 3. Підпис cookies
response.set_signed_cookie('visited', 'yes')

# 4. Password reset tokens
# Токени для скидання пароля

# 5. Криптографічний підпис
from django.core.signing import Signer
signer = Signer()
signed = signer.sign('my-value')
```

### Де використовується?
**Всередині Django** - ви його не бачите, але Django використовує постійно.

### Приклад:
```python
# settings.py
SECRET_KEY = 'django-secret-key-123'

# Django робить щось таке внутрішньо:
import hmac
import hashlib

def sign_data(data):
    signature = hmac.new(
        SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{data}:{signature}"

# Коли ви робите:
request.session['user_id'] = 5
# Django зберігає в cookie щось типу:
# sessionid=abc123:7a8f9b2c1d...  (підписано SECRET_KEY)
```

---

## 2️⃣ `JWT_SECRET_KEY`

### Що це?
Це **ваш кастомний ключ** для підпису JWT токенів (для API аутентифікації).

### Для чого використовується?
```python
# JWT токени для REST API

# 1. Генерація access токену
POST /api/auth/token/
Response: {"access": "eyJhbGci...", "refresh": "..."}

# 2. Валідація токену
Authorization: Bearer eyJhbGci...

# 3. Підпис payload
payload = {
    "user_id": 3,
    "username": "gala",
    "exp": 1762093974
}
# Підписується JWT_SECRET_KEY
```

### Де використовується?
**В REST API** - для JWT токенів між мікросервісами.

### Приклад:
```python
import jwt
from datetime import datetime, timedelta

JWT_SECRET_KEY = 'super-secret-jwt-key-123'

# Auth Service: Генерує токен
payload = {
    'user_id': 3,
    'username': 'gala',
    'exp': datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
# token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Books Service: Валідує токен
try:
    decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
    user_id = decoded['user_id']  # 3
except jwt.InvalidTokenError:
    return "Invalid token"
```

---

## 📊 Порівняльна таблиця:

| Параметр | `DJANGO_SECRET_KEY` | `JWT_SECRET_KEY` |
|----------|---------------------|------------------|
| **Призначення** | Django внутрішні операції | JWT токени для API |
| **Використовує** | Django framework | djangorestframework-simplejwt |
| **Що підписує** | Сесії, CSRF, cookies, password reset | Access/Refresh токени |
| **Область дії** | Один Django проєкт | Між мікросервісами |
| **Обов'язковий** | ✅ Так (Django не запуститься) | ✅ Так (для JWT) |
| **Може бути однаковий?** | ⚠️ Так, але не рекомендовано | |
| **Мікросервіси** | Кожен сервіс має свій | ⚠️ Має бути однаковий! |

---

## 🔍 Детальне пояснення:

### Сценарій 1: Традиційний Django (БЕЗ мікросервісів)

```python
# settings.py
SECRET_KEY = 'django-secret-key-123'

# Використовується для:
# ✅ Session cookies
# ✅ CSRF токени  
# ✅ Password reset
# ✅ Signed cookies

# JWT НЕ використовується (звичайна session-based аутентифікація)
```

### Сценарій 2: Django REST API (один сервіс)

```python
# settings.py
SECRET_KEY = 'django-secret-key-123'

SIMPLE_JWT = {
    'SIGNING_KEY': SECRET_KEY,  # ⚠️ Використовуємо той самий ключ
}

# Чому це працює:
# - Тільки один сервіс
# - JWT та Django в одному місці
# - Не треба синхронізувати ключі
```

### Сценарій 3: Мікросервіси (наш випадок) 🎯

```python
# Auth Service (Port 8001)
# settings.py
SECRET_KEY = 'django-auth-secret-123'  # Унікальний для Auth

SIMPLE_JWT = {
    'SIGNING_KEY': 'shared-jwt-secret',  # ⚠️ Спільний для ОБОХ!
}

# Books Service (Port 8002)  
# settings.py
SECRET_KEY = 'django-books-secret-456'  # Інший для Books!

SIMPLE_JWT = {
    'SIGNING_KEY': 'shared-jwt-secret',  # ⚠️ ТОЙ САМИЙ!
}
```

### Чому різні `SECRET_KEY`, але однаковий `JWT_SECRET_KEY`?

```
┌─────────────────────────────────────────────────────┐
│  Auth Service (Port 8001)                           │
│  DJANGO_SECRET_KEY = "auth-secret-123"              │
│  ↓                                                   │
│  Підписує: сесії, CSRF, cookies AUTH сервісу        │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
              JWT_SECRET_KEY = "shared-secret"
                          │
                          ▼ (Генерує JWT токен)
                  eyJhbGciOiJIUzI1NiI...
                          │
                          ▼ (Відправляє користувачу)
┌─────────────────────────────────────────────────────┐
│  Books Service (Port 8002)                          │
│  DJANGO_SECRET_KEY = "books-secret-456"             │
│  ↓                                                   │
│  Підписує: сесії, CSRF, cookies BOOKS сервісу       │
│                                                      │
│  JWT_SECRET_KEY = "shared-secret" ← ТОЙ САМИЙ!     │
│  ↓                                                   │
│  Валідує: eyJhbGciOiJIUzI1NiI...                   │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ Важливі моменти:

### ❌ Помилка 1: Однакові `DJANGO_SECRET_KEY`

```python
# Auth Service
SECRET_KEY = 'same-key-123'

# Books Service  
SECRET_KEY = 'same-key-123'  # ❌ ПОГАНО!
```

**Проблема:**
- Якщо зламають один сервіс, доступ до іншого теж відкритий
- CSRF токени одного сервісу працюють на іншому
- Порушення принципу ізоляції

### ❌ Помилка 2: Різні `JWT_SECRET_KEY`

```python
# Auth Service
JWT_SECRET_KEY = 'auth-jwt-key'

# Books Service
JWT_SECRET_KEY = 'books-jwt-key'  # ❌ НЕ ПРАЦЮЄ!
```

**Проблема:**
```python
# Auth генерує токен з 'auth-jwt-key'
token = jwt.encode(payload, 'auth-jwt-key')

# Books намагається валідувати з 'books-jwt-key'
jwt.decode(token, 'books-jwt-key')  # 💥 InvalidSignatureError!
```

### ✅ Правильно:

```bash
# .env
DJANGO_SECRET_KEY_AUTH=unique-auth-key-sdfsdf234
DJANGO_SECRET_KEY_BOOKS=unique-books-key-xcvxcv567
JWT_SECRET_KEY=shared-jwt-key-for-all-services-123456
```

```python
# Auth Service
SECRET_KEY = config('DJANGO_SECRET_KEY_AUTH')
JWT_SECRET = config('JWT_SECRET_KEY')  # Спільний

# Books Service
SECRET_KEY = config('DJANGO_SECRET_KEY_BOOKS')
JWT_SECRET = config('JWT_SECRET_KEY')  # Той самий!
```

---

## 🔐 Генерація безпечних ключів:

```python
# Генерація DJANGO_SECRET_KEY
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
# Output: 'django-insecure-x7f#2@k!9p$q&w*e...'

# Генерація JWT_SECRET_KEY
import secrets
print(secrets.token_urlsafe(64))
# Output: 'aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5...'

# Або через командний рядок
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 📝 Оновлений `.env`:

```bash
# ============================================
# Django Secret Keys (РІЗНІ для кожного сервісу)
# ============================================
DJANGO_SECRET_KEY_AUTH=auth-django-secret-sdaf2342sdfSDFSDF234sdf
DJANGO_SECRET_KEY_BOOKS=books-django-secret-xcvzxc567fghFGH567fgh

# ============================================
# JWT Secret Key (ОДНАКОВИЙ для всіх сервісів!)
# ============================================
JWT_SECRET_KEY=shared-jwt-secret-qwer1234asdfASDF5678zxcvZXCV9012
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# ============================================
# Other settings
# ============================================
DEBUG=True
```

### Оновлені `settings.py`:

**Auth Service:**
```python
SECRET_KEY = config('DJANGO_SECRET_KEY_AUTH')

SIMPLE_JWT = {
    'SIGNING_KEY': config('JWT_SECRET_KEY'),  # Спільний ключ
    # ...
}
```

**Books Service:**
```python
SECRET_KEY = config('DJANGO_SECRET_KEY_BOOKS')

SIMPLE_JWT = {
    'SIGNING_KEY': config('JWT_SECRET_KEY'),  # Той самий спільний ключ
    # ...
}
```

---

## 🎯 Підсумок:

| Ключ | Область дії | Унікальність | Мета |
|------|-------------|--------------|------|
| `DJANGO_SECRET_KEY` | Один Django проєкт | ✅ Унікальний для кожного сервісу | Django внутрішня безпека |
| `JWT_SECRET_KEY` | Між мікросервісами | ⚠️ Однаковий для всіх сервісів | Валідація JWT токенів |

**Золоте правило:**
- 🔴 `DJANGO_SECRET_KEY` → **різний** для кожного сервісу (ізоляція)
- 🟢 `JWT_SECRET_KEY` → **однаковий** для всіх сервісів (інтеграція)

**Аналогія:**
- `DJANGO_SECRET_KEY` = Ключ від вашої квартири (у кожної квартири свій)
- `JWT_SECRET_KEY` = Код від під'їзду (у всіх мешканців однаковий)

