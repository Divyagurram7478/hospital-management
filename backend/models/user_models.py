# JSON-like schema definitions (for reference) and convenient helpers
# Implementation is using pymongo and manual validation for clarity.

USER_SCHEMA = {
    "username": "string (unique)",
    "email": "string",
    "password": "bytes (bcrypt hashed)",
    "role": "string (admin|doctor|patient|nurse|receptionist)",
    "profile": {
        "first_name": "string",
        "last_name": "string",
        "phone": "string",
        "address": "string",
        "specialty": "string (for doctors)",
        "qualifications": "string",
    },
    "salary": "number (optional for staff)",
    "created_at": "datetime"
}
