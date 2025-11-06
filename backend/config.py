import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from the root .env file
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')

    # MongoDB URI (from your .env)
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/hospital_db')

    # Session lifetime
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Flask environment and debug mode
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
