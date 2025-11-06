PRESCRIPTION_SCHEMA = {
    "patient_id": "ObjectId",
    "doctor_id": "ObjectId",
    "medications": [
        {"name":"string","dose":"string","frequency":"string","duration":"string"}
    ],
    "notes": "string",
    "issued_at": "datetime"
}
