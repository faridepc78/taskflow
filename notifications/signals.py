from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import invalidate_unread_count_cache
from .models import Notification


@receiver(post_save, sender=Notification)
def invalidate_notification_cache_on_save(sender, instance, **kwargs):
    invalidate_unread_count_cache(instance.user_id)


@receiver(post_delete, sender=Notification)
def invalidate_notification_cache_on_delete(sender, instance, **kwargs):
    invalidate_unread_count_cache(instance.user_id)
