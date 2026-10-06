from ..models import Task


def change_task_status(*, task: Task, status: str) -> Task:
    if status not in Task.Status.values:
        raise ValueError("Invalid task status.")

    if task.status != status:
        task.status = status
        task.save(update_fields=["status", "updated_at"])

    return task
