"""
patients.py — Patient and visit record management
"""

from app.Db import get_cursor


def add_patient(name: str, phone: str) -> dict:
    """Add a new patient, or return existing one if phone already exists"""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM patients WHERE phone = %s", (phone,))
        existing = cur.fetchone()
        if existing:
            return existing

        cur.execute(
            "INSERT INTO patients (name, phone) VALUES (%s, %s) RETURNING *",
            (name, phone)
        )
        return cur.fetchone()


def get_patient_by_phone(phone: str) -> dict | None:
    """Find a patient by phone number"""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM patients WHERE phone = %s", (phone,))
        return cur.fetchone()


def add_visit(patient_id: int, treatment_done: str, notes: str = "") -> dict:
    """Log a new visit for a patient (today's date by default)"""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO visits (patient_id, treatment_done, notes)
               VALUES (%s, %s, %s) RETURNING *""",
            (patient_id, treatment_done, notes)
        )
        return cur.fetchone()


def get_visits_for_patient(patient_id: int) -> list[dict]:
    """Get all visit history for a patient, newest first"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT * FROM visits WHERE patient_id = %s
               ORDER BY visit_date DESC""",
            (patient_id,)
        )
        return cur.fetchall()


def get_todays_visits() -> list[dict]:
    """Get all patients who visited today, with their names"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT v.*, p.name, p.phone
               FROM visits v
               JOIN patients p ON v.patient_id = p.id
               WHERE v.visit_date = CURRENT_DATE
               ORDER BY v.created_at DESC"""
        )
        return cur.fetchall()


def add_appointment(patient_id: int, appointment_date: str, appointment_time: str, treatment: str) -> dict:
    """Schedule a new appointment for a patient"""
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO appointments (patient_id, appointment_date, appointment_time, treatment)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (patient_id, appointment_date, appointment_time, treatment)
        )
        return cur.fetchone()


def get_upcoming_appointments(patient_id: int) -> list[dict]:
    """Get all future booked appointments for a patient"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT * FROM appointments
               WHERE patient_id = %s AND status = 'Booked'
               AND appointment_date >= CURRENT_DATE
               ORDER BY appointment_date ASC""",
            (patient_id,)
        )
        return cur.fetchall()


def get_all_upcoming_appointments() -> list[dict]:
    """Get all upcoming appointments across all patients (for staff dashboard)"""
    with get_cursor() as cur:
        cur.execute(
            """SELECT a.*, p.name, p.phone
               FROM appointments a
               JOIN patients p ON a.patient_id = p.id
               WHERE a.status = 'Booked' AND a.appointment_date >= CURRENT_DATE
               ORDER BY a.appointment_date ASC, a.appointment_time ASC"""
        )
        return cur.fetchall()