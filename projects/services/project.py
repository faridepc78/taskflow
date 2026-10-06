from ..models import Project


def archive_project(project: Project) -> None:
    project.is_archived = True
    project.save(update_fields=["is_archived"])


def restore_project(project: Project) -> None:
    project.is_archived = False
    project.save(update_fields=["is_archived"])
