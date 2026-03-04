# Music Learning Academy

Multi-tenant SaaS platform for music academies to manage courses, lessons, live video sessions, and student progress.

## Tech Stack

- **Backend:** Django 4.2 + Django Channels (Daphne ASGI)
- **Frontend:** Django Templates + HTMX 2.0 + Tailwind CSS (CDN) + DaisyUI 4.12
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Cache/Broker:** Redis (Channels layer, Celery broker, cache)
- **Payments:** Stripe (checkout, subscriptions, webhooks)
- **Live Video:** Jitsi Meet (IFrame API, music-optimized audio)
- **Email:** SendGrid (SMTP)
- **Task Queue:** Celery + Celery Beat

## Features

- **Multi-tenancy** — shared DB with tenant isolation via academy FK
- **RBAC** — owner, instructor, student roles per academy
- **42 product features** across 4 releases (courses, enrollments, scheduling, practice, payments, music tools)
- **Production hardening** — rate limiting, security headers, structured logging, health checks, CI/CD

## Quick Start (Development)

```bash
# Clone and set up virtual environment
git clone <repo-url>
cd music_learning_academy
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements/dev.txt

# Run migrations and seed demo data
python manage.py migrate
python manage.py seed_demo_data

# Start dev server
python manage.py runserver 8001
```

Open http://localhost:8001 and log in with a demo account.

## Demo Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@harmonymusic.com | admin123 | Owner |
| sarah@harmonymusic.com | instructor123 | Instructor |
| david@harmonymusic.com | instructor123 | Instructor |
| alice@example.com | student123 | Student |
| bob@example.com | student123 | Student |
| carol@example.com | student123 | Student |

## Docker Deployment

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Build and start all services
docker compose up -d --build

# Services: postgres, redis, web (Daphne), nginx, celery-worker, celery-beat
```

## Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SECRET_KEY` | Yes | Django secret key (required in production) |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames |
| `STRIPE_SECRET_KEY` | For payments | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | For payments | Stripe webhook signing secret |
| `SENDGRID_API_KEY` | For email | SendGrid SMTP API key |
| `SENTRY_DSN` | Optional | Sentry error tracking DSN |
| `REDIS_URL` | Production | Redis connection for Channels |
| `CELERY_BROKER_URL` | Production | Redis connection for Celery |

## Testing

```bash
# Unit + integration tests (249 tests, ~74% coverage)
python -m pytest tests/unit tests/integration -v

# E2E tests (requires server running on port 8001)
python -m pytest tests/e2e -v

# With coverage report
python -m pytest tests/unit tests/integration --cov=apps --cov-report=html
```

## Project Structure

```
music_learning_academy/
├── config/              # Settings (base/dev/prod), URLs, ASGI/WSGI, Celery
├── apps/
│   ├── accounts/        # User, Membership, auth views
│   ├── academies/       # Academy, tenant middleware/mixins
│   ├── courses/         # Course, Lesson, PracticeAssignment
│   ├── enrollments/     # Enrollment, LessonProgress, submissions
│   ├── scheduling/      # LiveSession, Jitsi integration
│   ├── dashboards/      # Role-based dashboards
│   ├── notifications/   # Notifications, WebSocket consumer
│   ├── practice/        # PracticeLog, goals, streaks
│   ├── payments/        # Stripe, subscriptions, coupons, payouts
│   ├── music_tools/     # Metronome, tuner, ear training, AI feedback
│   ├── library/         # Content library (shared resources)
│   └── common/          # Base models, middleware, validators
├── templates/           # HTML templates (base.html + per-app)
├── static/              # CSS, JS
├── tests/               # unit/, integration/, e2e/
├── deployment/          # nginx.conf, SSL scripts
└── requirements/        # base.txt, dev.txt
```

## License

Proprietary. All rights reserved.
