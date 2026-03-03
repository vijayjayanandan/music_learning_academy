FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt \
    && pip install --no-cache-dir gunicorn psycopg2-binary channels-redis

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# Default: run Daphne ASGI server (supports HTTP + WebSocket)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
