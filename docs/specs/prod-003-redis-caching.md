# PROD-003: Redis Caching

## Status: Done

## Summary
LocMemCache for dev, Redis (DB 2) for prod. Dashboard stats cached 5min, stats partial 30s, with cache invalidation on course CRUD.

## Implementation
- Dev: `django.core.cache.backends.locmem.LocMemCache`
- Prod: `django_redis.cache.RedisCache` on `REDIS_URL` DB 2
- Dashboard admin/instructor/student views cache expensive aggregate queries for 5 minutes
- `DashboardStatsPartialView` caches for 30 seconds (HTMX polling interval)
- Course create/update/delete views invalidate dashboard cache keys
- Cache keys namespaced by academy slug to maintain tenant isolation

## Files Modified/Created
- `config/settings/base.py` — LocMemCache default config
- `config/settings/prod.py` — RedisCache config with DB 2
- `apps/dashboards/views.py` — `cache.get/set` on stats queries
- `apps/courses/views.py` — `cache.delete` on course CRUD operations

## Configuration
- `REDIS_URL` env var (prod) — defaults to `redis://localhost:6379`
- Cache DB is `/2` to avoid conflicts with Channels (DB 0) and Celery (DB 1)

## Verification
- Load dashboard, verify second load is faster (check Django debug toolbar or logs)
- Create a course, verify dashboard stats update immediately (cache invalidated)
