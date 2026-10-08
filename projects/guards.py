from django.http import Http404


def require_active_project(project):
    if project.is_archived:
        raise Http404("Archived projects are read-only. Restore the project to edit it.")
