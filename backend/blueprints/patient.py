from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..utils.decorators import roles_required
from bson.objectid import ObjectId
import datetime

patient_bp = Blueprint('patient', __name__, template_folder='../templates/patient')

# ------------------ Dashboard ------------------
@patient_bp.route('/')
@login_required
@roles_required('patient')
def dashboard():
    db = current_app.db
    patient = db.patients.find_one({'user_id': ObjectId(current_user.get_id())})
    appts = list(db.appointments.find({'patient_id': ObjectId(current_user.get_id())}))
    prescriptions = list(db.prescriptions.find({'patient_id': ObjectId(current_user.get_id())}))
    bills = list(db.billing.find({'patient_id': ObjectId(current_user.get_id())}))
    reports = list(db.reports.find({'patient_id': ObjectId(current_user.get_id())}))

    return render_template(
        'patient/dashboard.html',
        appointments=appts,
        prescriptions=prescriptions,
        bills=bills,
        reports=reports,
        patient=patient
    )

# ------------------ Book Appointment ------------------
@patient_bp.route('/book', methods=['GET', 'POST'])
@login_required
@roles_required('patient')
def book_appointment():
    db = current_app.db

    # 🩺 Preload doctors and problems
    doctors = list(db.users.find({'role': 'doctor'}, {'password': 0}))
    problems = [
        {'name': 'Fever'}, {'name': 'Cold & Cough'}, {'name': 'Chest Pain'}, {'name': 'Skin Rash'},
        {'name': 'Headache'}, {'name': 'Stomach Pain'}, {'name': 'Joint Pain'}, {'name': 'Vision Problem'},
        {'name': 'Toothache'}, {'name': 'Ear Pain'}, {'name': 'Diabetes Checkup'}, {'name': 'Heart Checkup'},
        {'name': 'Allergy'}, {'name': 'High Blood Pressure'}, {'name': 'Back Pain'}
    ]

    specialist_map = {
        'Fever': 'General Physician', 'Cold & Cough': 'General Physician',
        'Chest Pain': 'Cardiologist', 'Skin Rash': 'Dermatologist',
        'Headache': 'Neurologist', 'Stomach Pain': 'Gastroenterologist',
        'Joint Pain': 'Orthopedic', 'Vision Problem': 'Ophthalmologist',
        'Toothache': 'Dentist', 'Ear Pain': 'ENT Specialist',
        'Diabetes Checkup': 'Endocrinologist', 'Heart Checkup': 'Cardiologist',
        'Allergy': 'Allergist', 'High Blood Pressure': 'Cardiologist',
        'Back Pain': 'Orthopedic'
    }

    if request.method == 'POST':
        problem = request.form.get('problem')
        if problem == 'other':
            problem = request.form.get('other_problem')

        doctor_id = request.form.get('doctor')
        date = request.form.get('date')
        time = request.form.get('time')
        suggested_specialist = specialist_map.get(problem, 'General Physician')

        appointment_datetime = datetime.datetime.fromisoformat(f"{date}T{time}")

        appt = {
            'problem': problem,
            'doctor_id': ObjectId(doctor_id),
            'patient_id': ObjectId(current_user.get_id()),
            'status': 'pending',
            'datetime': appointment_datetime,
            'created_at': datetime.datetime.utcnow()
        }

        db.appointments.insert_one(appt)

        # 💰 Automatically create a billing record
        doctor = db.users.find_one({'_id': ObjectId(doctor_id)}, {'username': 1})
        appointment_fee = 500  # default consultation fee

        db.billing.insert_one({
            'patient_id': ObjectId(current_user.get_id()),
            'doctor_id': ObjectId(doctor_id),
            'doctor_name': doctor.get('username', 'Unknown Doctor') if doctor else 'Unknown Doctor',
            'amount': appointment_fee,
            'status': 'Unpaid',
            'description': f"Consultation for {problem}",
            'date': datetime.datetime.utcnow(),
            'appointment_datetime': appointment_datetime,
            'created_at': datetime.datetime.utcnow()
        })

        flash(f"Appointment booked successfully! Based on your problem ('{problem}'), "
              f"you should meet a {suggested_specialist}. A bill of ₹{appointment_fee} has been generated.",
              'success')

        return redirect(url_for('patient.book_appointment'))

    appointments = list(db.appointments.find({'patient_id': ObjectId(current_user.get_id())}))
    doctor_map = {str(d['_id']): d for d in doctors}

    for a in appointments:
        a['doctor_id'] = str(a['doctor_id'])

    return render_template(
        'patient/book_appointment.html',
        problems=problems,
        doctors=doctors,
        appointments=appointments,
        doctor_map=doctor_map
    )

# ------------------ Cancel Appointment ------------------
@patient_bp.route('/cancel/<appt_id>', methods=['POST'])
@login_required
@roles_required('patient')
def cancel_appointment(appt_id):
    db = current_app.db
    db.appointments.update_one(
        {'_id': ObjectId(appt_id), 'patient_id': ObjectId(current_user.get_id())},
        {'$set': {'status': 'cancelled'}}
    )
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('patient.dashboard'))

# ------------------ Profile Update ------------------
@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@roles_required('patient')
def profile():
    db = current_app.db
    user_id = ObjectId(current_user.get_id())

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        db.patients.update_one(
            {'user_id': user_id},
            {'$set': {'name': name, 'email': email, 'phone': phone, 'address': address}},
            upsert=True
        )

        db.users.update_one(
            {'_id': user_id},
            {'$set': {'email': email, 'name': name}}
        )

        flash('Profile updated.', 'success')
        return redirect(url_for('patient.profile'))

    patient = db.patients.find_one({'user_id': user_id})
    return render_template('patient/profile.html', patient=patient)

# ------------------ View Prescriptions ------------------
@patient_bp.route('/prescriptions')
@login_required
@roles_required('patient')
def prescriptions():
    db = current_app.db
    patient_id = current_user.get_id()
    prescriptions = list(db.prescriptions.find({"patient_id": ObjectId(patient_id)}))

    for p in prescriptions:
        p["_id"] = str(p.get("_id"))
        p["doctor_name"] = p.get("doctor_name") or "Unknown"
        p["diagnosis"] = p.get("diagnosis") or "N/A"
        p["medicines"] = p.get("medicines") or "N/A"
        p["instructions"] = p.get("instructions") or "N/A"
        created_at = p.get("created_at")
        if created_at and isinstance(created_at, datetime.datetime):
            p["date"] = created_at.strftime("%Y-%m-%d %H:%M")
        elif created_at and isinstance(created_at, str):
            p["date"] = created_at
        else:
            p["date"] = "N/A"

    return render_template('patient/prescriptions.html', prescriptions=prescriptions)

# ------------------ View Reports ------------------
@patient_bp.route('/reports')
@login_required
@roles_required('patient')
def reports():
    db = current_app.db
    reports = list(db.reports.find({'patient_id': ObjectId(current_user.get_id())}))
    return render_template('patient/reports.html', reports=reports)

# ------------------ View Billing ------------------
@patient_bp.route('/billing')
@login_required
@roles_required('patient')
def billing():
    db = current_app.db
    bills = list(db.billing.find({'patient_id': ObjectId(current_user.get_id())}))

    for b in bills:
        b['_id'] = str(b.get('_id'))
        b['date'] = b.get('date').strftime("%Y-%m-%d %H:%M") if b.get('date') else 'N/A'

    return render_template('patient/billing.html', bills=bills)

# ------------------ Pay Bill ------------------
@patient_bp.route('/billing/pay/<bill_id>', methods=['POST'])
@login_required
@roles_required('patient')
def pay_bill(bill_id):
    db = current_app.db
    db.billing.update_one(
        {'_id': ObjectId(bill_id), 'patient_id': ObjectId(current_user.get_id())},
        {'$set': {'status': 'Paid'}}
    )
    flash('✅ Payment successful! Your bill is now marked as Paid.', 'success')
    return redirect(url_for('patient.billing'))
