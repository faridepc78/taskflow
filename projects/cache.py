from django.core.cache import cache

DASHBOARD_STATS_CACHE_TIMEOUT = 300


def get_dashboard_stats_cache_key(user_id: int) -> str:
    return f"dashboard_stats:user:{user_id}"


def invalidate_dashboard_stats_cache(user_id: int) -> None:
    cache.delete(get_dashboard_stats_cache_key(user_id))
