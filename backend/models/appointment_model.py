from datetime import datetime
from bson.objectid import ObjectId

class Appointment:
    def __init__(self, patient_id, doctor_id, date, time, status='Pending'):
        self.patient_id = ObjectId(patient_id)
        self.doctor_id = ObjectId(doctor_id)
        self.date = date
        self.time = time
        self.status = status  # 'Pending', 'Accepted', or 'Rejected'
        self.created_at = datetime.utcnow()
