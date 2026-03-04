"""Shared cache invalidation utilities."""

from django.core.cache import cache


def invalidate_dashboard_cache(academy_pk):
    """Clear all cached dashboard stats for an academy."""
    cache.delete(f"admin_dashboard_stats_{academy_pk}")
    cache.delete(f"stats_partial_owner_{academy_pk}")
    # Instructor stats use per-user keys — delete_pattern not available in LocMemCache,
    # so these expire naturally after 30s. For Redis in prod, consider using delete_pattern.
