from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                return HttpResponseForbidden("You do not have permission to perform this action.")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def admin_required(view_func):
    return role_required("admin")(view_func)


def teacher_required(view_func):
    return role_required("teacher")(view_func)
