from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import TaskAttachment


@receiver(post_delete, sender=TaskAttachment)
def delete_attachment_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
