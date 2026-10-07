from django.core.cache import cache

UNREAD_COUNT_CACHE_TIMEOUT = 300


def get_unread_count_cache_key(user_id: int) -> str:
    return f"notifications:unread_count:user:{user_id}"


def invalidate_unread_count_cache(user_id: int) -> None:
    cache.delete(get_unread_count_cache_key(user_id))
