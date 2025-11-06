from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..utils.decorators import roles_required
from bson.objectid import ObjectId

nurse_bp = Blueprint('nurse', __name__, template_folder='../templates/nurse')

# Dashboard
@nurse_bp.route('/')
@login_required
@roles_required('nurse')
def dashboard():
    db = current_app.db

    assignments = list(db.nurse_assignments.find({'nurse_id': str(current_user.get_id())}))
    schedule = list(db.nurse_schedule.find({'nurse_id': str(current_user.get_id())}))
    salary = db.salaries.find_one({'nurse_id': str(current_user.get_id())})

    return render_template(
        'nurse/dashboard.html',
        assignments=assignments,
        schedule=schedule,
        salary=salary
    )


# Schedule management
@nurse_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
@roles_required('nurse')
def schedule():
    db = current_app.db
    if request.method == 'POST':
        shift_date = request.form['date']
        shift_time = request.form['time']
        db.nurse_schedule.insert_one({
            'nurse_id': str(current_user.get_id()),
            'date': shift_date,
            'time': shift_time
        })
        flash("Shift added successfully!", "success")
        return redirect(url_for('nurse.schedule'))

    shifts = list(db.nurse_schedule.find({'nurse_id': str(current_user.get_id())}))
    return render_template('nurse/schedule.html', shifts=shifts)

# Apply for leave
@nurse_bp.route('/leave', methods=['GET', 'POST'])
@login_required
@roles_required('nurse')
def leave():
    db = current_app.db
    if request.method == 'POST':
        date = request.form['date']
        reason = request.form['reason']
        db.leave_requests.insert_one({
            'nurse_id': str(current_user.get_id()),
            'date': date,
            'reason': reason,
            'status': 'Pending'
        })
        flash("Leave request submitted!", "info")
        return redirect(url_for('nurse.leave'))

    requests = list(db.leave_requests.find({'nurse_id': str(current_user.get_id())}))
    return render_template('nurse/leave.html', requests=requests)

# Salary details
@nurse_bp.route('/salary')
@login_required
@roles_required('nurse')
def salary():
    db = current_app.db
    salary = db.users.find_one(
        {"_id": ObjectId(current_user.get_id())},
        {"salary": 1, "updated_at": 1, "_id": 0}
    )

    return render_template('nurse/salary.html', salary=salary)

# Profile
from bson.objectid import ObjectId

@nurse_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@roles_required('nurse')
def profile():
    db = current_app.db

    if request.method == 'POST':
        updated_data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "address": request.form.get("address"),
        }

        # ✅ update fields directly on user, not inside "profile"
        db.users.update_one(
            {"_id": ObjectId(current_user.get_id())},
            {"$set": updated_data}
        )

        flash("Profile updated successfully!", "success")
        return redirect(url_for("nurse.profile"))

    # ✅ fetch updated user (without password)
    user = db.users.find_one(
        {"_id": ObjectId(current_user.get_id())},
        {"password": 0}
    )

    return render_template("nurse/profile.html", user=user)
