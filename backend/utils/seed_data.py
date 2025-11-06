# minimal seeding script to create an admin and sample users
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
import os
from config import Config

def seed():
    client = MongoClient(Config.MONGO_URI)
    db = client.get_default_database()
    if db.users.count_documents({'role':'admin'}) == 0:
        admin_pw = bcrypt.hashpw("AdminPass123!".encode('utf-8'), bcrypt.gensalt())
        db.users.insert_one({
            'username': 'admin',
            'email': 'admin@hospital.example',
            'password': admin_pw,
            'role': 'admin',
            'profile': {'first_name':'Admin','last_name':'User'},
            'salary': 0
        })
        print("Admin created: username=admin password=AdminPass123!")
    else:
        print("Admin already exists")

    # add sample doctor
    if db.users.count_documents({'username':'drsmith'}) == 0:
        pw = bcrypt.hashpw("Doctor123!".encode('utf-8'), bcrypt.gensalt())
        db.users.insert_one({
            'username': 'drsmith',
            'email': 'drsmith@hospital.example',
            'password': pw,
            'role': 'doctor',
            'profile': {'first_name':'John','last_name':'Smith','specialty':'Cardiology'},
            'salary': 120000
        })
        print("Doctor drsmith created")

    # sample patient
    if db.users.count_documents({'username':'patient1'}) == 0:
        pw = bcrypt.hashpw("Patient123!".encode('utf-8'), bcrypt.gensalt())
        db.users.insert_one({
            'username': 'patient1',
            'email': 'patient1@hospital.example',
            'password': pw,
            'role': 'patient',
            'profile': {'first_name':'Jane','last_name':'Doe'},
            'salary': 0
        })
        print("Patient patient1 created")

if __name__ == '__main__':
    seed()
