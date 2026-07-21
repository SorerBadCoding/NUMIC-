from .models import Notification


def notify_users(users, notif_type, title, body="", link=""):
    users = list({u.id: u for u in users}.values())
    Notification.objects.bulk_create([
        Notification(user=u, notif_type=notif_type, title=title, body=body, link=link)
        for u in users
    ])


def notify_all_students(notif_type, title, body="", link=""):
    from accounts.models import User

    notify_users(User.objects.filter(role=User.Role.STUDENT), notif_type, title, body, link)


def notify_section_students(section, notif_type, title, body="", link=""):
    from accounts.models import User

    students = User.objects.filter(enrollments__section=section)
    notify_users(students, notif_type, title, body, link)
