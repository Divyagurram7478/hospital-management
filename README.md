# Hospital Management System (Flask + MongoDB)

Professional hospital management system scaffold with role-based dashboards (Doctor, Patient, Admin, Nurse, Receptionist).

## Features
- Role-based authentication (Flask-Login)
- MongoDB backend (pymongo / mongoengine style models)
- Appointments, prescriptions, billing, reports
- CRUD for users and schedules
- Corporate-grade UI with separate navigation per role
- Environment-based config and production-ready gunicorn example

## Prerequisites
- Python 3.10+
- MongoDB instance (local or Atlas)
- Node (optional, only if you extend frontend tooling)

## Quickstart (development)
1. Clone / copy project into folder.
2. Create a Python venv:
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
3. Install Python dependencies:
pip install -r backend/requirements.txt
4. Copy `.env.example` -> `.env` and set:
FLASK_ENV=development
SECRET_KEY=your-secret-key
MONGO_URI=mongodb://localhost:27017/hospital_db
5. Seed minimal data (optional):
python backend/utils/seed_data.py
6. Run app (development):
cd backend
flask run

or

python app.py7. Visit `http://127.0.0.1:5000/`

## Production
- Use gunicorn with `gunicorn_config.py`, environment variables, and set `FLASK_ENV=production`.
- Use HTTPS, proper secrets management, and a managed MongoDB or Atlas cluster.

## Structure
- `backend/` - Flask app, templates and blueprints
- `frontend/static` - static assets (css/js/images)
- `backend/models` - MongoDB models (Python)
- `backend/blueprints` - modules for each user role

## Notes
- Templates reference static files at `/static/...`. Verify `app.static_folder` if needed.
- Replace Google Maps embed in `templates/index.html` with your API or embed link (file `frontend/google_maps_embed.txt` contains example).

