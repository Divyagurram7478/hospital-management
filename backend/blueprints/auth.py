from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import bcrypt
import datetime

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# --------------------
# User Class
# --------------------
from flask_login import UserMixin

from flask_login import UserMixin
from flask import current_app

class User(UserMixin):
    """
    Small wrapper around the Mongo user document that integrates with Flask-Login.
    Use User.from_mongo(doc, app) to construct — from_mongo is a classmethod to
    accept an optional app param.
    """
    def __init__(self, user_dict, app=None):
        # store string id for Flask-Login get_id()
        self._id = str(user_dict.get('_id'))
        self.username = user_dict.get('username')
        self.email = user_dict.get('email')
        self.role = user_dict.get('role')
        self.profile = user_dict.get('profile', {}) or {}
        self._user = user_dict
        # keep reference to app if needed
        self.app = app or current_app

    def get_id(self):
        return self._id

    @classmethod
    def from_mongo(cls, user_dict, app=None):
        """
        Create a User instance from a mongo document.
        Accepts an optional app argument; using classmethod makes calls like
        User.from_mongo(user, current_app) valid.
        """
        return cls(user_dict, app=app)


# --------------------
# LOGIN (UPDATED)
# --------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Role-aware login — user can only log in from their own role page.
    If mismatched, show an invalid message instead of redirecting.
    """
    if request.method == 'POST':
        db = current_app.db
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        expected_role = request.form.get('expected_role', '').lower()  # ✅ fixed name

        if not username or not password:
            flash('Enter username and password', 'warning')
            return redirect(request.referrer or url_for('auth.login'))

        user = db.users.find_one({'username': username})
        if not user:
            flash('Invalid username or password', 'danger')
            return redirect(request.referrer or url_for('auth.login'))

        stored_pw = user.get('password')
        try:
            if isinstance(stored_pw, (bytes, bytearray)):
                pw_ok = bcrypt.checkpw(password.encode('utf-8'), stored_pw)
            else:
                pw_ok = bcrypt.checkpw(password.encode('utf-8'), stored_pw.encode('utf-8'))
        except Exception as e:
            pw_ok = False
            current_app.logger.exception("Password verification failed: %s", e)

        if not pw_ok:
            flash('Invalid username or password', 'danger')
            return redirect(request.referrer or url_for('auth.login'))

        # ✅ Verify role strictly
        user_role = (user.get('role') or '').lower()
        if expected_role and expected_role != user_role:
            flash(f"Invalid credentials: You are a '{user_role}' trying to log in as '{expected_role}'.", 'danger')
            return redirect(request.referrer or url_for('auth.login'))

        # ✅ Login success
        user_obj = User.from_mongo(user, current_app)
        login_user(user_obj)

        role_routes = {
            'admin': 'admin.dashboard',
            'doctor': 'doctor.dashboard',
            'patient': 'patient.dashboard',
            'nurse': 'nurse.dashboard',
            'receptionist': 'receptionist.dashboard'
        }
        endpoint = role_routes.get(user_role, 'auth.login')
        return redirect(url_for(endpoint))

    # GET — Render login page
    role = request.args.get('role', '')
    return render_template('login.html', role=role)

# --------------------
# LOGOUT
# --------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --------------------
# REGISTER
# --------------------
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        db = current_app.db
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'patient')  # default patient

        if db.users.find_one({'username': username}):
            flash("Username already exists", "danger")
        else:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_doc = {
                'username': username,
                'email': email,
                'password': hashed,
                'role': role,
                'profile': {},
                'salary': 0,
                'created_at': datetime.datetime.utcnow()
            }
            result = db.users.insert_one(user_doc)

            # Create linked profile in role-specific collections
            if role == 'patient':
                db.patients.insert_one({
                    'user_id': result.inserted_id,
                    'name': username,
                    'email': email,
                    'phone': '',
                    'address': '',
                    'created_at': datetime.datetime.utcnow()
                })
            elif role == 'doctor':
                db.doctors.insert_one({
                    'user_id': result.inserted_id,
                    'name': username,
                    'email': email,
                    'specialty': '',
                    'salary': 0,
                    'created_at': datetime.datetime.utcnow()
                })
            elif role == 'nurse':
                db.nurses.insert_one({
                    'user_id': result.inserted_id,
                    'name': username,
                    'email': email,
                    'shift': '',
                    'salary': 0,
                    'created_at': datetime.datetime.utcnow()
                })
            elif role == 'receptionist':
                db.receptionists.insert_one({
                    'user_id': result.inserted_id,
                    'name': username,
                    'email': email,
                    'phone': '',
                    'created_at': datetime.datetime.utcnow()
                })


            flash("Registered. Please login", "success")
            return redirect(url_for('auth.login', role=role))
    
    return render_template('register.html')

