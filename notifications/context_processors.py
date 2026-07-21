def notifications_context(request):
    if not request.user.is_authenticated:
        return {}
    recent = request.user.notifications.all()[:6]
    unread_count = request.user.notifications.filter(is_read=False).count()
    return {
        "nav_notifications": recent,
        "nav_unread_count": unread_count,
    }
