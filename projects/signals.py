from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from accounts.models import Profile

from .middleware import get_current_actor
from .models import Activity, Category, Project, Task, TaskAttachment

TRACKED_MODELS = (User, Profile, Project, Category, Task, TaskAttachment)
IGNORED_FIELDS = {
    "password",
    "last_login",
    "date_joined",
    "created_at",
    "updated_at",
    "uploaded_at",
}


def _serialize(value):
    if isinstance(value, Model):
        return value.pk
    if isinstance(value, FieldFile):
        return value.name or None
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    return value


def _snapshot(instance):
    values = {}
    for field in instance._meta.concrete_fields:
        if field.primary_key or field.name in IGNORED_FIELDS:
            continue
        values[field.name] = _serialize(getattr(instance, field.name))
    return values


def _display_value(instance, field_name, value):
    try:
        field = instance._meta.get_field(field_name)
    except FieldDoesNotExist:
        return value

    if field.choices:
        return dict(field.flatchoices).get(value, value)
    return value


def _subject_name(instance):
    if isinstance(instance, User):
        return instance.get_full_name() or instance.username
    if isinstance(instance, TaskAttachment):
        return instance.filename
    return str(instance)


def _project_for(instance):
    if isinstance(instance, Project):
        return instance
    if isinstance(instance, Task):
        return instance.project
    if isinstance(instance, TaskAttachment):
        return instance.task.project
    return None


def _task_for(instance):
    if isinstance(instance, Task):
        return instance
    if isinstance(instance, TaskAttachment):
        return instance.task
    return None


def _pretty_changes(instance, changes):
    pretty = {}
    for name, values in changes.items():
        pretty[name] = {
            "from": _display_value(instance, name, values.get("from")),
            "to": _display_value(instance, name, values.get("to")),
        }
    return pretty


def _description(instance, action, changes=None):
    model_name = instance._meta.verbose_name.title()
    name = _subject_name(instance)

    if action == Activity.Action.CREATED:
        return f'Created {model_name} "{name}".'

    if action == Activity.Action.DELETED:
        return f'Deleted {model_name} "{name}".'

    changes = changes or {}

    if isinstance(instance, Project) and set(changes) == {"is_archived"}:
        action_name = "Archived" if instance.is_archived else "Restored"
        return f'{action_name} Project "{name}".'

    if isinstance(instance, Task) and set(changes) == {"status"}:
        values = changes["status"]
        return f'Changed Task "{name}" status from {values["from"]} to {values["to"]}.'

    fields = ", ".join(name.replace("_", " ") for name in changes)
    suffix = f" ({fields})" if fields else ""

    return f'Updated {model_name} "{name}"{suffix}.'


def _create_activity(instance, action, *, changes=None, description=None):
    if isinstance(instance, Activity):
        return

    pretty_changes = _pretty_changes(instance, changes or {})

    Activity.objects.create(
        project=_project_for(instance),
        task=_task_for(instance),
        actor=get_current_actor(),
        action=action,
        subject_type=instance._meta.label,
        subject_id=str(instance.pk or ""),
        subject_name=_subject_name(instance),
        description=description or _description(instance, action, pretty_changes),
        changes=pretty_changes,
    )


@receiver(pre_save)
def capture_old_values(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS or not instance.pk:
        return

    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    instance._activity_old_values = _snapshot(old)


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS:
        return

    if created:
        _create_activity(instance, Activity.Action.CREATED)
        return

    old_values = getattr(instance, "_activity_old_values", {})
    new_values = _snapshot(instance)

    changes = {
        name: {"from": old_values.get(name), "to": value}
        for name, value in new_values.items()
        if old_values.get(name) != value
    }

    if changes:
        _create_activity(
            instance,
            Activity.Action.UPDATED,
            changes=changes,
        )


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    if sender in TRACKED_MODELS:
        _create_activity(instance, Activity.Action.DELETED)


@receiver(post_delete, sender=TaskAttachment)
def delete_attachment_file(sender, instance, **kwargs):
    if instance.file:
        Path(instance.file.path).unlink(missing_ok=True)


@receiver(m2m_changed, sender=Task.categories.through)
def log_task_categories(sender, instance, action, pk_set, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    if action == "post_clear":
        detail = "Cleared all categories"
        changes = {
            "categories": {
                "from": "assigned",
                "to": [],
            }
        }
    else:
        category_names = list(
            Category.objects.filter(pk__in=pk_set or set()).values_list(
                "name", flat=True
            )
        )

        verb = "Added" if action == "post_add" else "Removed"
        detail = f"{verb} categories {', '.join(category_names)}"

        changes = {
            "categories": {
                "from": None,
                "to": category_names,
            }
        }

    _create_activity(
        instance,
        Activity.Action.RELATION_CHANGED,
        changes=changes,
        description=f'{detail} on Task "{instance.title}".',
    )
