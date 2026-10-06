from contextvars import ContextVar

_current_actor = ContextVar("taskflow_activity_actor", default=None)


def get_current_actor():
    return _current_actor.get()


class ActivityActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        actor = (
            request.user
            if getattr(request, "user", None) and request.user.is_authenticated
            else None
        )
        token = _current_actor.set(actor)
        try:
            return self.get_response(request)
        finally:
            _current_actor.reset(token)
