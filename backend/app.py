from flask import Flask, render_template, redirect, url_for, current_app
from backend.config import Config
from flask_login import LoginManager, current_user
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Blueprints will import db object from app context via current_app
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="../frontend/static")
    app.config.from_object(Config)

    # Setup MongoDB client and attach to app
    client = MongoClient(app.config['MONGO_URI'])
    app.db_client = client
    app.db = client.get_default_database()
    print("✅ Connected to MongoDB Atlas successfully!")

    # Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from backend.blueprints.auth import auth_bp, User
    from backend.blueprints.admin import admin_bp
    from backend.blueprints.doctor import doctor_bp
    from backend.blueprints.patient import patient_bp
    from backend.blueprints.nurse import nurse_bp
    from backend.blueprints.receptionist import receptionist_bp
    from bson.objectid import ObjectId


    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(nurse_bp, url_prefix='/nurse')
    app.register_blueprint(receptionist_bp, url_prefix='/receptionist')

    @login_manager.user_loader
    def load_user(user_id):
        u = current_app.db.users.find_one({"_id": ObjectId(user_id)})
        if u:
            return User.from_mongo(u)
        return None


    @app.route('/')
    def index():
        hospital = {
            'name': "Aegis Care Hospital",
            'email': "info@aegiscare.example",
            'phone': "+1 (555) 123-4567",
            'address': "123 Wellness Avenue, Health City",
            'logo': url_for('static', filename='images/logo.png')
        }
        return render_template('index.html', hospital=hospital)

    # simple health route
    @app.route('/health')
    def health():
        return {"status":"ok"}

    return app

if __name__ == '__main__':
    app = create_app()
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    app.run(host=host, port=port, debug=app.config['DEBUG'])
