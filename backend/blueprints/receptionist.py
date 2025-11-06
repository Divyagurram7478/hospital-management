from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
from ..utils.decorators import roles_required

receptionist_bp = Blueprint('receptionist', __name__)


# ---------------- Dashboard ----------------
@receptionist_bp.route('/dashboard')
@login_required
def dashboard():
    db = current_app.db
    schedules = list(db.schedules.find())
    return render_template('receptionist/dashboard.html', schedules=schedules)


# ---------------- Profile ----------------
@receptionist_bp.route('/profile')
@login_required
def profile():
    return render_template('receptionist/profile.html', user=current_user)


# ---------------- Schedule ----------------
@receptionist_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
@roles_required('receptionist')
def schedule_page():
    db = current_app.db

    # 🟩 If the user submitted the form
    if request.method == 'POST':
        doctor = request.form['doctor']
        patient = request.form['patient']
        date = request.form['date']
        time = request.form['time']
        status = request.form['status']

        # 🟩 Insert into MongoDB
        db.schedules.insert_one({
            'doctor': doctor,
            'patient': patient,
            'date': date,
            'time': time,
            'status': status
        })

        flash('Schedule added successfully!', 'success')
        return redirect(url_for('receptionist.schedule_page'))  # reload page after insert

    # 🟦 If it's a GET request (show the page)
    schedules = list(db.schedules.find())
    return render_template('receptionist/schedule.html', schedules=schedules)


# ---------------- Salary ----------------
@receptionist_bp.route('/salary')
@login_required
def salary_page():   # renamed
    db = current_app.db
    salary_records = list(db.salaries.find({"user_id": current_user.get_id()}))
    return render_template('receptionist/salary.html', salaries=salary_records)


# ---------------- Call Logs ----------------
@receptionist_bp.route('/call_logs')
@login_required
def call_logs_page():   # renamed
    db = current_app.db
    logs = list(db.calllogs.find())
    return render_template('receptionist/call_logs.html', call_logs=logs)
