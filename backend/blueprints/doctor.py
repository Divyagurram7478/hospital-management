from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from bson.objectid import ObjectId
from datetime import datetime
from ..utils.decorators import roles_required

# ---------------- Blueprint ---------------- #
doctor_bp = Blueprint('doctor', __name__, template_folder='../templates/doctor')


# ---------------- Dashboard ---------------- #
@doctor_bp.route('/', endpoint='dashboard')
@login_required
@roles_required('doctor')
def dashboard():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())

    appts = list(db.appointments.find({'doctor_id': doctor_id}).sort('datetime', 1))
    for a in appts:
        a['_id'] = str(a['_id'])
        patient_doc = db.patients.find_one({'_id': ObjectId(a['patient_id'])}) if a.get('patient_id') else None
        a['patient_name'] = patient_doc.get('name') if patient_doc else 'Unknown'
        a['status'] = a.get('status', 'pending').capitalize()

    return render_template('doctor/dashboard.html', appointments=appts)


# ---------------- Appointments ---------------- #
@doctor_bp.route('/appointments')
@login_required
@roles_required('doctor')
def doctor_appointments():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())
    appointments = list(db.appointments.find({'doctor_id': doctor_id}))

    for appt in appointments:
        patient = db.users.find_one({'_id': appt.get('patient_id')})
        appt['_id'] = str(appt['_id'])
        appt['patient_name'] = patient.get('name') if patient else 'Unknown'
        appt['status'] = appt.get('status', 'Pending').capitalize()

        if "datetime" in appt and not isinstance(appt["datetime"], datetime):
            try:
                appt["datetime"] = datetime.strptime(appt["datetime"], "%Y-%m-%dT%H:%M")
            except:
                appt["datetime"] = None

    return render_template('doctor/appointments.html', appointments=appointments)


@doctor_bp.route('/appointments/<appt_id>/status', methods=['POST'])
@login_required
@roles_required('doctor')
def doctor_update_status(appt_id):
    db = current_app.db
    new_status = request.form.get('status')

    if new_status not in ['Accepted', 'Rejected']:
        flash('Invalid status ❌', 'danger')
        return redirect(url_for('doctor.doctor_appointments'))

    db.appointments.update_one(
        {'_id': ObjectId(appt_id), 'doctor_id': ObjectId(current_user.get_id())},
        {'$set': {'status': new_status.lower()}}
    )
    flash(f'Appointment marked as {new_status}', 'success')
    return redirect(url_for('doctor.doctor_appointments'))


# ---------------- Patients (Accepted Only) ---------------- #
@doctor_bp.route('/patients')
@login_required
@roles_required('doctor')
def patients():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())

    accepted_appts = list(db.appointments.find({
        "doctor_id": doctor_id,
        "status": "accepted"
    }))

    if not accepted_appts:
        return render_template('doctor/patients.html', patients=[])

    patient_ids = [appt['patient_id'] for appt in accepted_appts]
    patients = list(db.users.find({"_id": {"$in": patient_ids}}))

    combined_data = []
    for appt in accepted_appts:
        for patient in patients:
            if patient["_id"] == appt["patient_id"]:
                combined_data.append({
                    "id": str(patient["_id"]),
                    "name": patient.get("name"),
                    "email": patient.get("email"),
                    "problem": appt.get("problem", "N/A"),
                    "datetime": appt.get("datetime"),
                    "status": appt.get("status", "unknown")
                })

    return render_template('doctor/patients.html', patients=combined_data)


# ---------------- Add Prescription ---------------- #
@doctor_bp.route('/add_prescription/<patient_id>')
@login_required
@roles_required('doctor')
def add_prescription(patient_id):
    db = current_app.db
    patient = db.users.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        flash("Patient not found!", "danger")
        return redirect(url_for('doctor.patients'))
    return render_template('doctor/add_prescription.html', patient=patient)


# ---------------- Save Prescription ---------------- #

@doctor_bp.route('/save_prescription/<patient_id>', methods=['POST'])
@login_required
@roles_required('doctor')
def save_prescription(patient_id):
    db = current_app.db

    diagnosis = request.form.get('diagnosis')
    medicines = request.form.get('medicines')
    instructions = request.form.get('instructions')

    # ✅ Correctly get doctor name
    profile = getattr(current_user, 'profile', {})
    first_name = profile.get('first_name', '').strip()
    last_name = profile.get('last_name', '').strip()
    doctor_name = f"{first_name} {last_name}".strip() or "Unknown"

    # ✅ Safe and simple specialization (won’t break anything)
    specialization = profile.get('specialization', 'General')

    # ✅ Save real datetime
    prescription = {
        "patient_id": patient_id if isinstance(patient_id, ObjectId) else ObjectId(patient_id),
        "doctor_id": ObjectId(current_user.get_id()),
        "doctor_name": doctor_name,
        "specialization": specialization,
        "diagnosis": diagnosis or "N/A",
        "medicines": medicines or "N/A",
        "instructions": instructions or "N/A",
        "created_at": datetime.now()
    }

    # ✅ Insert into DB
    db.prescriptions.insert_one(prescription)

    flash('Prescription added successfully!', 'success')
    return redirect(url_for('doctor.patients'))


# ---------------- View Prescriptions ---------------- #
@doctor_bp.route('/view_prescriptions')
@login_required
@roles_required('doctor')
def view_prescriptions():
    db = current_app.db
    doctor_id = ObjectId(current_user.get_id())

    prescriptions = list(db.prescriptions.find({"doctor_id": doctor_id}).sort("created_at", -1))
    for p in prescriptions:
        p["_id"] = str(p["_id"])
        
        # Fetch patient name safely
        patient = db.users.find_one({"_id": p["patient_id"]})
        p["patient_name"] = patient.get("name", "Unknown") if patient else "Unknown"

        # Handle both datetime and string date
        created_at = p.get("created_at", None)
        if isinstance(created_at, datetime):
            p["created_at"] = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            p["created_at"] = created_at or datetime.now().strftime("%Y-%m-%d %H:%M")

    return render_template("doctor/view_prescriptions.html", prescriptions=prescriptions)



# ---------------- Profile ---------------- #
@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@roles_required('doctor')
def profile():
    db = current_app.db
    if request.method == 'POST':
        profile_data = dict(request.form)
        db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'profile': profile_data}})
        flash('Profile updated ✅', 'success')

    user = db.users.find_one({'_id': ObjectId(current_user.get_id())}, {'password': 0})
    return render_template('doctor/profile.html', user=user)


# ---------------- Salary ---------------- #
@doctor_bp.route('/salary')
@login_required
@roles_required('doctor')
def salary():
    db = current_app.db
    doctor = db.users.find_one({'_id': ObjectId(current_user.get_id())})
    salary = doctor.get('salary', 'Not set')
    return render_template('doctor/salary.html', salary=salary)


# ---------------- Logout ---------------- #
@doctor_bp.route('/logout')
@login_required
@roles_required('doctor')
def logout():
    logout_user()
    flash("You have been logged out 👋", "info")
    return redirect(url_for('auth.login'))
