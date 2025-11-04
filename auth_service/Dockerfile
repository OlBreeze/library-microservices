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