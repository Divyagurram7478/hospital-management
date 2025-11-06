from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def roles_required(*roles):
    """
    Restrict route access to specific user roles (case-insensitive).
    Example:
        @roles_required("admin", "doctor")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login", next=request.url))

            # normalize both sides to lowercase
            allowed_roles = [r.lower() for r in roles]
            user_role = (current_user.role or "").lower()

            if user_role not in allowed_roles:
                flash("Permission denied. You do not have access to this page.", "danger")
                # redirect based on user role
                if user_role == "doctor":
                    return redirect(url_for("doctor.dashboard"))
                elif user_role == "patient":
                    return redirect(url_for("patient.dashboard"))
                elif user_role == "nurse":
                    return redirect(url_for("nurse.dashboard"))
                elif user_role == "receptionist":
                    return redirect(url_for("receptionist.dashboard"))
                elif user_role == "admin":
                    return redirect(url_for("admin.dashboard"))
                else:
                    return redirect(url_for("auth.login"))

            return fn(*args, **kwargs)
        return wrapper
    return decorator
