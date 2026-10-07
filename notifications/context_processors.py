from .selectors import get_unread_notification_count


def notifications(request):
    if not request.user.is_authenticated:
        return {"notification_unread_count": 0}

    return {
        "notification_unread_count": get_unread_notification_count(request.user),
    }
