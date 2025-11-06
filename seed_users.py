import bcrypt
from pymongo import MongoClient

# Connect to Mongo
client = MongoClient("mongodb://localhost:27017/")
db = client["hospital_db"]

# Clear old users (⚠️ this deletes existing users)
db.users.drop()

# User accounts with plaintext passwords (we’ll hash them below)
users = [
    {
        "username": "doctor1",
        "password": "password123",
        "role": "doctor",
        "profile": {
            "first_name": "John",
            "last_name": "Doe",
            "specialty": "Cardiology"
        }
    },
    {"username": "patient1", "password": "password123", "role": "patient"},
    {"username": "nurse1", "password": "password123", "role": "nurse"},
    {"username": "reception1", "password": "password123", "role": "receptionist"},
    {"username": "admin", "password": "admin123", "role": "admin"},
]

# Insert users with hashed passwords
for user in users:
    if db.users.find_one({"username": user["username"]}):
        print(f"User {user['username']} already exists, skipping...")
    else:
        hashed = bcrypt.hashpw(user["password"].encode("utf-8"), bcrypt.gensalt())
        user["password"] = hashed  # store hashed password
        db.users.insert_one(user)
        print(f"Inserted user {user['username']}")
