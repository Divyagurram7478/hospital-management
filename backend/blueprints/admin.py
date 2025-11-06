from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..utils.decorators import roles_required
from bson.objectid import ObjectId
import datetime

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

def _get_current_user_oid():
    """
    Safely obtain the ObjectId for the logged-in user.
    Returns ObjectId or None (or raw id if not an ObjectId string).
    """
    uid = None
    try:
        uid = current_user.get_id()
    except Exception:
        uid = getattr(current_user, 'id', None)

    if not uid:
        return None
    try:
        return ObjectId(uid)
    except Exception:
        return uid


# ------------------ Dashboard ------------------ #
@admin_bp.route('/')
@login_required
@roles_required('admin')
def dashboard():
    db = current_app.db
    users = list(db.users.find({}, {"password": 0}))
    counts = {
        'doctors': db.users.count_documents({'role': 'doctor'}),
        'patients': db.users.count_documents({'role': 'patient'}),
        'nurses': db.users.count_documents({'role': 'nurse'}),
        'receptionists': db.users.count_documents({'role': 'receptionist'}),
        'appointments': db.appointments.count_documents({})
    }

    # Revenue aggregation (safe)
    try:
        raw_revenue = list(db.payments.aggregate([
            {"$group": {
                "_id": {"year": {"$year": "$date"}, "month": {"$month": "$date"}},
                "total": {"$sum": "$amount"}
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]))
    except Exception as e:
        raw_revenue = []
        current_app.logger.warning("Revenue aggregation error: %s", e)

    # Convert aggregation output to simple {label: "YYYY-MM", total: number}
    revenue = []
    for r in raw_revenue:
        try:
            y = r['_id'].get('year')
            m = r['_id'].get('month')
            label = f"{int(y)}-{int(m):02d}"
        except Exception:
            label = str(r.get('_id'))
        revenue.append({"label": label, "total": r.get('total', 0)})

    # Doctor salaries: include username & salary
    salaries = list(db.users.find({"role": "doctor"}, {"salary": 1, "username": 1}))

    return render_template(
        'admin/dashboard.html',
        title="Admin Dashboard",
        users=users,
        counts=counts,
        revenue=revenue,
        salaries=salaries
    )


# ------------------ Manage Users ------------------ #
@admin_bp.route('/manage_users', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def manage_users():
    db = current_app.db

    if request.method == 'POST':
        action = request.form.get("action")
        try:
            if action == "create":
                # Optional: accept password field (if provided) — omitted here for admin convenience
                db.users.insert_one({
                    "username": request.form["username"],
                    "email": request.form["email"],
                    "role": request.form["role"],
                    "salary": float(request.form.get("salary", 0)),
                    "created_at": datetime.datetime.utcnow()
                })
                flash("User created successfully", "success")

            elif action == "delete":
                db.users.delete_one({"_id": ObjectId(request.form["user_id"])})
                flash("User deleted successfully", "info")

            elif action == "update":
                db.users.update_one(
                    {"_id": ObjectId(request.form["user_id"])},
                    {"$set": {
                        "username": request.form["username"],
                        "email": request.form["email"],
                        "role": request.form["role"],
                        "salary": float(request.form.get("salary", 0)),
                        "updated_at": datetime.datetime.utcnow()
                    }}
                )
                flash("User updated successfully", "success")
        except Exception as e:
            current_app.logger.exception("Manage users action failed")
            flash("Operation failed: " + str(e), "danger")
        return redirect(url_for('admin.manage_users'))

    users = list(db.users.find({}, {"password": 0}))
    return render_template(
        'admin/manage_users.html',
        title="Manage Users",
        users=users
    )


# ------------------ Rulebook ------------------ #
@admin_bp.route('/rules', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def rules():
    db = current_app.db
    rules_doc = db.rules.find_one({}) or {"content": ""}

    if request.method == 'POST':
        try:
            content = request.form.get('content', '')
            db.rules.update_one({}, {"$set": {"content": content, "updated_at": datetime.datetime.utcnow()}}, upsert=True)
            flash("Rulebook updated successfully", "success")
        except Exception as e:
            current_app.logger.exception("Failed updating rulebook")
            flash("Failed to update rulebook: " + str(e), "danger")
        return redirect(url_for('admin.rules'))

    return render_template(
        'admin/rules.html',
        title="Admin Rulebook",
        rules=rules_doc
    )


# ------------------ Entries / Biometric ------------------ #
@admin_bp.route('/entries')
@login_required
@roles_required('admin')
def entries():
    db = current_app.db
    logs = list(db.entries.find().sort("timestamp", -1).limit(200))
    return render_template(
        'admin/entries.html',
        title="Admin Entries",
        logs=logs
    )


# ------------------ Admin Profile ------------------ #
@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def profile():
    db = current_app.db

    if request.method == 'POST':
        try:
            user_oid = _get_current_user_oid()
            if user_oid:
                db.users.update_one(
                    {"_id": user_oid},
                    {"$set": {
                        "username": request.form.get("username"),
                        "email": request.form.get("email"),
                        "updated_at": datetime.datetime.utcnow()
                    }}
                )
                flash("Profile updated successfully", "success")
            else:
                flash("Unable to determine current user id", "danger")
        except Exception as e:
            current_app.logger.exception("Failed to update profile")
            flash("Profile update failed: " + str(e), "danger")
        return redirect(url_for('admin.profile'))

    return render_template(
        'admin/profile.html',
        title="Admin Profile",
        user=current_user
    )
