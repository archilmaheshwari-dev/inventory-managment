"""
main.py — Staff dashboard web app
Patient records, appointments, inventory and billing
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from functools import wraps
import os

from app.Patients import (
    add_patient, get_patient_by_phone, add_visit, get_visits_for_patient,
    get_todays_visits, add_appointment, get_upcoming_appointments,
    get_all_upcoming_appointments
)
from app.Inventory import (
    add_medicine, restock_medicine, get_all_medicines, get_medicine_by_name,
    create_sale, get_sale_details, get_sales_for_patient, get_low_stock_medicines
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-this")

STAFF_USERNAME = os.getenv("STAFF_USERNAME", "admin")
STAFF_PASSWORD = os.getenv("STAFF_PASSWORD", "admin123")


def login_required(f):
    """Decorator to protect routes that need staff login"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Authentication ───────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == STAFF_USERNAME and password == STAFF_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    todays_visits = get_todays_visits()
    upcoming = get_all_upcoming_appointments()
    low_stock = get_low_stock_medicines()
    return render_template(
        "dashboard.html",
        todays_visits=todays_visits,
        upcoming=upcoming,
        low_stock=low_stock
    )


# ── Patient Records ───────────────────────────────────────────────────

@app.route("/patients/new", methods=["GET", "POST"])
@login_required
def new_patient():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        patient = add_patient(name, phone)
        return redirect(url_for("patient_detail", patient_id=patient["id"]))
    return render_template("new_patient.html")


@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    visits = get_visits_for_patient(patient_id)
    appointments = get_upcoming_appointments(patient_id)
    sales = get_sales_for_patient(patient_id)
    return render_template(
        "patient_detail.html",
        patient_id=patient_id,
        visits=visits,
        appointments=appointments,
        sales=sales
    )


@app.route("/patients/<int:patient_id>/visit", methods=["POST"])
@login_required
def log_visit(patient_id):
    treatment = request.form.get("treatment")
    notes = request.form.get("notes", "")
    add_visit(patient_id, treatment, notes)
    return redirect(url_for("patient_detail", patient_id=patient_id))


@app.route("/patients/<int:patient_id>/appointment", methods=["POST"])
@login_required
def schedule_appointment(patient_id):
    date = request.form.get("date")
    time = request.form.get("time")
    treatment = request.form.get("treatment")
    add_appointment(patient_id, date, time, treatment)
    return redirect(url_for("patient_detail", patient_id=patient_id))


# ── Inventory ──────────────────────────────────────────────────────────

@app.route("/inventory")
@login_required
def inventory_list():
    medicines = get_all_medicines()
    return render_template("inventory.html", medicines=medicines)


@app.route("/inventory/add", methods=["POST"])
@login_required
def add_inventory():
    name = request.form.get("name")
    price = float(request.form.get("price"))
    stock = int(request.form.get("stock", 0))
    add_medicine(name, price, stock)
    return redirect(url_for("inventory_list"))


@app.route("/inventory/restock/<int:medicine_id>", methods=["POST"])
@login_required
def restock(medicine_id):
    quantity = int(request.form.get("quantity"))
    restock_medicine(medicine_id, quantity)
    return redirect(url_for("inventory_list"))


# ── Billing ────────────────────────────────────────────────────────────

@app.route("/patients/<int:patient_id>/bill", methods=["GET", "POST"])
@login_required
def create_bill(patient_id):
    if request.method == "POST":
        medicine_ids = request.form.getlist("medicine_id")
        quantities = request.form.getlist("quantity")
        discount = float(request.form.get("discount", 0))

        items = [
            {"medicine_id": int(mid), "quantity": int(qty)}
            for mid, qty in zip(medicine_ids, quantities) if int(qty) > 0
        ]

        try:
            sale = create_sale(patient_id, items, discount)
            return redirect(url_for("view_invoice", sale_id=sale["id"]))
        except ValueError as e:
            medicines = get_all_medicines()
            return render_template("create_bill.html", patient_id=patient_id, medicines=medicines, error=str(e))

    medicines = get_all_medicines()
    return render_template("create_bill.html", patient_id=patient_id, medicines=medicines)


@app.route("/invoice/<int:sale_id>")
@login_required
def view_invoice(sale_id):
    sale = get_sale_details(sale_id)
    return render_template("invoice.html", sale=sale)


# ── Health check ─────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "Clinic system running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)