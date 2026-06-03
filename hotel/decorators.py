from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect("hotel:login")
            if request.user.role not in allowed_roles:
                messages.error(request, "You do not have permission to access this page.")
                if request.user.role == "guest":
                    return redirect("hotel:guest_dashboard")
                elif request.user.role == "staff":
                    return redirect("hotel:staff_dashboard")
                elif request.user.role == "manager":
                    return redirect("hotel:manager_dashboard")
                return redirect("hotel:home")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def guest_required(view_func):
    return role_required(["guest"])(view_func)


def staff_required(view_func):
    return role_required(["staff"])(view_func)


def manager_required(view_func):
    return role_required(["manager"])(view_func)
