from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Notification


@login_required
def notifications_list(request):
    notifs = list(request.user.notifications.all())
    unread_ids = [n.id for n in notifs if not n.is_read]
    if unread_ids:
        Notification.objects.filter(id__in=unread_ids).update(is_read=True)

    return render(request, "notifications/list.html", {"active_nav": "notifications", "notifications": notifs})
