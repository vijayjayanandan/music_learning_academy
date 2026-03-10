# ADR-006: Cache Strategy — Redis vs Alternatives (2026)

**Date:** 2026-03-10
**Status:** DECIDED
**Decision:** Stay with Redis. No migration needed.

---

## Context

The Music Academy platform uses Redis for caching aggregate dashboard statistics and analytics queries. The question: *Is Redis the right choice long-term, or should we evaluate alternatives?*

### Current State
- **Cache backend (dev):** `LocMemCache` (in-process)
- **Cache backend (prod):** Redis (shared across instances)
- **Cache keys:** 7 active (dashboard stats, analytics aggregates, health check)
- **Memory footprint:** ~10 MB for 100 academies
- **Hit rate:** ~70-85% (estimated)
- **Infrastructure cost:** $0 local, $26-52/mo AWS ElastiCache

### Constraints
- Multi-instance deployment (stateless app servers)
- Tenant isolation required (per-academy cache keys)
- Cold-start performance critical (owner first login)
- PostgreSQL for persistent DB
- Docker-based local development

---

## Alternatives Evaluated

### 1. PostgreSQL Materialized Views
**Concept:** Denormalized table refreshed on mutation, indexed for fast reads.

```sql
CREATE MATERIALIZED VIEW dashboard_stats AS
SELECT academy_id,
       COUNT(DISTINCT user_id) FILTER (WHERE role='student') as total_students,
       COUNT(DISTINCT user_id) FILTER (WHERE role='instructor') as total_instructors,
       COUNT(*) FILTER (WHERE model='Course' AND is_published) as total_courses
FROM memberships m
LEFT JOIN courses c ON m.academy_id = c.academy_id
GROUP BY m.academy_id;

CREATE INDEX ON dashboard_stats(academy_id);
```

**Pros:**
- No new infrastructure (native PostgreSQL)
- Indexed for fast lookups (0ms latency, not 1-3ms network)
- ACID guarantees (consistency)
- Triggers can auto-refresh on mutations
- Schema-managed (migrations handle view creation)

**Cons:**
- Requires PostgreSQL (not SQLite in dev, breaks SQLite-dev-path)
- Requires test DB to be PostgreSQL (slower test suite)
- Manual trigger management (easy to miss invalidation)
- No TTL (either always stale or always refreshing)
- View refresh locks table (brief, but possible lock contention)
- Materialized view refresh is all-or-nothing (can't cache per-academy)

**Technical Risk:** MEDIUM
- Locks on refresh could cause timeout during heavy load
- Per-academy caching is harder with views (need union of multiple views)
- Migration complexity (can't easily add/remove views)

**Cost:** $0 (uses existing DB)

**Verdict:** **Good as secondary layer with Redis**, not primary replacement. Avoids cold-start (matview always exists) but adds operational complexity.

---

### 2. Memcached
**Concept:** Memory-only, fast, simple K-V store (older than Redis).

**Pros:**
- Simpler than Redis (no Pub/Sub complexity)
- Slightly faster for pure K-V (no extra command parsing)
- Same operational model as Redis
- Can run same container with Django (test-friendly)

**Cons:**
- No persistence (cold-start = full cache miss)
- No data structures (only strings)
- Abandoned project (last release 2021, no active maintainers)
- Same memory overhead as Redis (64 MB minimum)
- No automatic TTL cleanup (uses LRU eviction)

**Technical Risk:** LOW (well-proven, stable)

**Cost:** $0 local, $13-26/mo AWS

**Verdict:** **Not worth switching.** Same cost and complexity as Redis, older and smaller ecosystem. If you're changing cache backends, DragonflyDB is strictly better.

---

### 3. DragonflyDB
**Concept:** Redis clone, written in C++, 5-10x faster single-threaded, drop-in compatible.

**Pros:**
- 100% Redis protocol (zero code changes needed)
- 5-10x faster than Redis for high concurrency
- Better memory efficiency
- Modern implementation (released 2022)
- Persistence support (RDB/AOF like Redis)
- Can self-host for $0 or use managed service

**Cons:**
- Newer project (less battle-tested than Redis)
- Smaller ecosystem
- Managed service (Dragonfly Cloud) only available via SaaS ($30/mo)
- Production users exist but community is smaller

**Technical Risk:** LOW (production-ready for 2+ years)

**Cost:** $0 self-hosted, $30/mo managed

**Verdict:** **Good future migration path.** If Redis becomes bottleneck, one-line config change to Dragonfly with same API. Not urgent now.

---

### 4. AWS ElastiCache (Managed Redis)
**Concept:** AWS-managed Redis with automatic failover, patching, monitoring.

**Pros:**
- Fully managed (no ops overhead)
- Automatic failover to standby (high availability)
- Automatic security updates
- Built-in CloudWatch monitoring
- Encryption at rest + in-transit
- Can scale without downtime (replica -> primary promotion)

**Cons:**
- Expensive for small scale ($26/mo minimum, doubles if HA)
- Cold-start: 5-10 minutes to launch
- AWS lock-in (difficult to migrate away)
- Over-engineered for <1000 users

**Technical Risk:** NONE (battle-tested at massive scale)

**Cost:** $26/mo single-node, $52/mo HA (multi-AZ)

**Verdict:** **Good once on AWS with 1000+ academies.** Overkill for current scale. Self-hosted Redis costs zero.

---

### 5. CloudFlare Cache
**Concept:** HTTP caching at CDN edge (caches entire responses).

**Pros:**
- Caches at HTTP level (fewer origin requests)
- Works for both static + dynamic content
- Serves stale if origin down (resilience)
- Massive geographic distribution (fast for global users)

**Cons:**
- Caches entire HTML (not suitable for personalized dashboards)
- Cache invalidation is complex (purge APIs, manual rules)
- TTL rules are all-or-nothing
- HTMX views need explicit `Cache-Control: no-cache` headers
- Not suitable for authenticated, user-specific content

**Technical Risk:** MEDIUM (requires careful cache-control headers)

**Cost:** Free (Cloudflare Free tier) or $200+/mo (Enterprise)

**Verdict:** **Good supplementary layer for public pages only** (landing page, pricing, etc.). NOT for authenticated dashboards. Use together with Redis, not instead.

---

### 6. Application-Level Python Caching (In-Memory Dict)

**Concept:** Cache logic as Python class with TTL tracking.

```python
class DashboardCache:
    _data = {}
    _timestamps = {}

    @classmethod
    def get(cls, key):
        if key in cls._data and time.time() - cls._timestamps[key] < 300:
            return cls._data[key]
        return None

    @classmethod
    def set(cls, key, value):
        cls._data[key] = value
        cls._timestamps[key] = time.time()
```

**Pros:**
- Fastest possible (in-process memory, no network)
- Zero external dependencies
- Works immediately in dev + prod
- Simple to debug

**Cons:**
- Lost on server restart (no persistence)
- Not shared between app instances (breaks with load balancing)
- No automatic TTL (manual eviction needed)
- Will cause stale data bugs (TTL not enforced, easy to forget)
- Violates stateless architecture principle

**Technical Risk:** CRITICAL (data consistency, hard to debug)

**Cost:** $0

**Verdict:** **Not suitable for production.** Fine for MVP/demo, but breaks immediately with multi-instance deployment.

---

### 7. Local Disk Cache (SQLite File)

**Concept:** Persistent K-V store on local app server disk.

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/django_cache",
    }
}
```

**Pros:**
- Persistent across restarts
- Faster than Redis (local I/O, no network)
- Works with single app server
- $0 cost

**Cons:**
- File I/O slower than memory (single thread bottleneck)
- Not shared between servers (sticky sessions required)
- File locking issues under concurrency
- Doesn't work with stateless/containerized deployments
- Violates cloud-native principles

**Technical Risk:** MEDIUM (works for single-server only)

**Cost:** $0

**Verdict:** **Not recommended for SaaS.** Works for single-server PoC, fails immediately when adding second instance.

---

### 8. DuckDB (Analytical Cache Layer)

**Concept:** Embedded OLAP database optimized for aggregations.

**Pros:**
- Designed for GROUP BY/SUM/COUNT (faster than relational DB)
- Can run in-process or as service
- Persistent snapshots
- Great for analytics-heavy workloads

**Cons:**
- Overkill for simple K-V caching
- Requires manual sync from main DB
- Another service to operate + maintain
- Not suitable for frequently-changing data

**Technical Risk:** MEDIUM (adds architectural complexity)

**Cost:** $0 self-hosted

**Verdict:** **Consider for future analytics warehouse, not as cache replacement.** Could be secondary layer for trend queries.

---

## Decision: Stay with Redis

### Why Redis Wins

| Criteria | Redis | Best Alternative | Winner |
|----------|-------|------------------|--------|
| **Setup** | 0 min | Matviews: 1 hour | Redis |
| **Cost** | $0-50/mo | Matviews: $0 | Tie |
| **Scalability** | Unlimited users | Matviews: Limited (MVCC) | Redis |
| **Flexibility** | Full cache control | Matviews: Rigid schema | Redis |
| **Operational load** | Minimal | Matviews: Moderate (triggers) | Redis |
| **Cold-start** | Empty after restart | Matviews: Always populated | Matviews (slight win) |
| **Already implemented** | ✓ | ✗ | Redis |

### Cost-Benefit Analysis

**Cost of keeping Redis:**
- Development: $0 (local instance)
- Production (small): $0-26/mo AWS (single instance)
- Production (scaling): $26-52/mo AWS (HA)
- Engineering effort: $0 (already implemented)
- **Annual cost:** $0-650

**Cost of switching to PostgreSQL Matviews:**
- Development: $200 (more complex test setup)
- Production: $0 (uses existing DB)
- Engineering effort: $2000 (8 hours × $250/hr)
- Risk: Triggers can break (5% chance of bugs)
- **Annual cost:** $200 + risk

**Cost of switching to DragonflyDB:**
- Development: $0 (one-line config change)
- Production: $0-30/mo
- Engineering effort: $200 (1 hour migration)
- Risk: Smaller ecosystem
- **Annual cost:** $0-360

**Verdict:** **ROI of switching: Negative.** Not worth $2000 engineering time to save $0/year.

---

## Implementation (No Changes Required)

Current setup is optimal:

### Development (Already Good)
```python
# config/settings/dev.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
```

Rationale: In-memory cache is fast for dev, restart clears stale data.

### Production (Already Good)
```python
# config/settings/prod.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://localhost:6379/2"),
    }
}
```

Rationale: Redis is persistent, shared, and scales.

### Cache Key Strategy (Already Good)
```python
# Tenant-scoped keys ensure no cross-academy pollution
cache_key = f"admin_dashboard_stats_{academy_pk}"

# TTLs match data freshness requirements
cache.set(cache_key, stats, 300)  # 5 min for dashboards
cache.set(cache_key, stats, 3600)  # 1 hour for analytics
```

### Cache Invalidation (Already Good)
```python
# Invalidate on mutations
def invalidate_dashboard_cache(academy_pk):
    cache.delete(f"admin_dashboard_stats_{academy_pk}")
    cache.delete(f"stats_partial_owner_{academy_pk}")
```

---

## Future Paths (If Requirements Change)

### Path A: Cold-Start Optimization (Add Matviews as Secondary Layer)

If cold-start performance matters (owner first login):

```python
# Use matview to warm cache on first load
def admin_dashboard_view(request):
    academy = get_academy(request)

    # Try cache first (warm path)
    cache_key = f"admin_dashboard_stats_{academy.pk}"
    stats = cache.get(cache_key)

    if stats is None:
        # Fall back to matview (cold path)
        stats = DashboardStats.objects.get(academy_id=academy.pk)
        cache.set(cache_key, stats._asdict(), 300)

    return render(request, "dashboard.html", stats)
```

**Cost:** 4 hours to implement matview + trigger logic.

### Path B: Faster Single-Threaded Performance (Migrate to DragonflyDB)

If benchmarks show Redis throughput is limiting:

```python
# One-line change to existing cache config
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "dragonfly://localhost:6379/2",  # Change here only
    }
}
```

**Cost:** 1 hour to test + deploy. API is 100% compatible.

### Path C: Fully Managed Cache (Migrate to AWS ElastiCache)

If you're on AWS and scale to 10k+ users:

```python
# Update env var in Render/AWS
REDIS_CACHE_URL = "redis://cache.abc123.ng.0001.use1.cache.amazonaws.com:6379/2"
# Zero code changes
```

**Cost:** 30 minutes setup time.

---

## Alternatives Explicitly NOT Recommended

1. **Memcached:** Same cost, older, no persistence. Use Redis or DragonflyDB instead.
2. **DuckDB:** Wrong tool (analytics DB, not cache). Use for future warehouse, not cache.
3. **Application dict:** Breaks with load balancing. Use Redis instead.
4. **File cache:** Slow and non-sharable. Use Redis instead.
5. **Matviews only:** Complex to maintain, no TTL. Use as secondary with Redis.

---

## Monitoring & Alerts (Recommended)

Ensure cache is working as intended:

```python
# Add to health check
def cache_health():
    try:
        cache.set("_health_check", "ok", 10)
        return "healthy" if cache.get("_health_check") == "ok" else "unhealthy"
    except Exception as e:
        return f"failed: {e}"

# Add metrics to dashboard
redis_info = redis_client.info('stats')
hit_rate = redis_info['hits'] / (redis_info['hits'] + redis_info['misses'])
memory_mb = redis_info['used_memory'] / 1024 / 1024

# Alert thresholds
if hit_rate < 0.5:  # Hit rate dropped below 50%
    alert("Cache hit rate degrading — check for TTL/invalidation issues")
if memory_mb > 500:  # Cache growing beyond 500MB
    alert("Cache memory exceeded — check for memory leaks")
```

---

## Decision Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Use Redis in prod?** | **YES** | Already optimized, zero cost, scales well |
| **Replace Redis now?** | **NO** | No business case; engineering cost >> benefit |
| **Consider DragonflyDB later?** | **YES** | One-line change if throughput becomes issue |
| **Add Matviews as secondary?** | **LATER** | Good for cold-start, defer until needed |
| **Switch to ElastiCache?** | **LATER** | Good for AWS lock-in + scale, defer until 10k+ users |
| **Use Memcached?** | **NO** | Same cost, worse than Redis |
| **Use application dict?** | **NO** | Breaks with multi-instance |
| **Use local file cache?** | **NO** | Non-shareable, violates stateless |
| **Use DuckDB?** | **MAYBE LATER** | As analytics warehouse, not cache |

---

## Conclusion

**Redis is the right choice for Music Academy.**

It solves real performance problems (analytics queries would be slow without it), has zero setup cost, scales to 1M+ users, and integrates seamlessly with Django.

The alternatives either:
- Solve non-existent problems (you don't have a cold-start issue)
- Add complexity for $0 savings (matviews, DuckDB)
- Require external infrastructure (ElastiCache)
- Are unsuitable for multi-instance deployments (file cache, app dict)

**Action:** No changes needed. Document this decision and revisit annually or when one of the "Future Paths" becomes relevant (cold-start matters, throughput matters, AWS scaling matters).
