# ADR-001: Shared-Database Multi-Tenancy via Academy FK

## Status
Accepted

## Context
Music Learning Academy is a SaaS platform where multiple academies share the same deployment. We needed a multi-tenancy strategy that balances isolation, complexity, and cost.

**Options considered:**
1. **Separate databases per tenant** — strongest isolation but operationally complex (migrations, backups, connection pooling per tenant)
2. **Separate schemas** (PostgreSQL) — good isolation but Django ORM doesn't natively support schema switching; requires `django-tenants`
3. **Shared database with tenant FK** — simplest, all data in one DB, isolated by filtering on `academy_id`

## Decision
Shared database with `academy` FK on all tenant-scoped models.

- `apps/common/models.py` defines `TenantScopedModel` abstract base with `academy = ForeignKey(Academy)`
- `apps/academies/middleware.py` sets `request.academy` from `request.user.current_academy`
- `apps/academies/mixins.py` provides `TenantMixin` that auto-filters querysets by `request.academy`

## Consequences

**Gains:**
- Simplest to implement and maintain — standard Django ORM, no third-party tenant library
- Single migration path, single backup, single connection pool
- Cross-tenant queries possible (needed for platform-level analytics later)
- Works with SQLite in development

**Risks:**
- Every query must remember to filter by academy — forgotten filters = data leak
- Mitigated by: `TenantMixin` on views, `TenantScopedModel` base, tenant isolation tests (`test_tenant_isolation.py`)
- No database-level isolation — a bug can expose cross-tenant data
- Performance: all tenants share indexes (acceptable at current scale)

**If we outgrow this:**
- Migrate to `django-tenants` (schema-based) when we have 100+ academies
- The `academy` FK pattern makes migration straightforward — just move tables into schemas
