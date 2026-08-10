from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response
)

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps
from datetime import datetime
import csv
import io
import re
import os


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

INSTANCE_DIR = os.path.join(
    BASE_DIR,
    "instance"
)

os.makedirs(
    INSTANCE_DIR,
    exist_ok=True
)

DATABASE_PATH = os.path.join(
    INSTANCE_DIR,
    "roster.db"
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL"
)

if DATABASE_URL:

    # Render / PostgreSQL compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    if DATABASE_URL.startswith("postgresql://"):
        # psycopg2 is normally used by SQLAlchemy if installed.
        # Keep the URL as provided.
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

else:

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + DATABASE_PATH
    )


db = SQLAlchemy(app)


# ============================================================
# DAYS
# ============================================================

DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
]


# ============================================================
# EMAIL SENDER
# ============================================================

try:

    from email_sender import send_roster_email

except Exception as exc:

    print(
        f"Email sender could not be loaded: {exc}"
    )

    def send_roster_email(**kwargs):
        return False


# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(160),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="employee",
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    rosters = db.relationship(
        "Roster",
        backref="employee",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Roster(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    week_start = db.Column(
        db.String(10),
        nullable=False
    )

    monday = db.Column(
        db.String(80),
        default="OFF"
    )

    monday_location = db.Column(
        db.String(200),
        default=""
    )

    tuesday = db.Column(
        db.String(80),
        default="OFF"
    )

    tuesday_location = db.Column(
        db.String(200),
        default=""
    )

    wednesday = db.Column(
        db.String(80),
        default="OFF"
    )

    wednesday_location = db.Column(
        db.String(200),
        default=""
    )

    thursday = db.Column(
        db.String(80),
        default="OFF"
    )

    thursday_location = db.Column(
        db.String(200),
        default=""
    )

    friday = db.Column(
        db.String(80),
        default="OFF"
    )

    friday_location = db.Column(
        db.String(200),
        default=""
    )

    saturday = db.Column(
        db.String(80),
        default="OFF"
    )

    saturday_location = db.Column(
        db.String(200),
        default=""
    )

    sunday = db.Column(
        db.String(80),
        default="OFF"
    )

    sunday_location = db.Column(
        db.String(200),
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# DATE HELPER
# ============================================================

def normalize_week_start(value):

    value = (value or "").strip()

    if not value:

        raise ValueError(
            "Week starting date is required."
        )

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y"
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt
            ).strftime("%Y-%m-%d")

        except ValueError:
            pass

    raise ValueError(
        f"Invalid week starting date: {value}. "
        "Please use YYYY-MM-DD."
    )


# ============================================================
# SHIFT HOURS
# ============================================================

def calculate_shift_hours(shift):

    if not shift:
        return 0

    shift = str(shift).strip()

    if shift.upper() == "OFF":
        return 0

    match = re.match(
        r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$",
        shift
    )

    if not match:
        return 0

    start_hour = int(match.group(1))
    start_minute = int(match.group(2))

    end_hour = int(match.group(3))
    end_minute = int(match.group(4))

    if (
        start_hour > 23
        or end_hour > 23
        or start_minute > 59
        or end_minute > 59
    ):
        return 0

    start_minutes = (
        start_hour * 60
        + start_minute
    )

    end_minutes = (
        end_hour * 60
        + end_minute
    )

    if end_minutes < start_minutes:
        end_minutes += 24 * 60

    total_minutes = (
        end_minutes - start_minutes
    )

    return round(
        total_minutes / 60,
        2
    )


def calculate_weekly_hours(roster):

    total = 0

    for day in DAYS:

        shift = getattr(
            roster,
            day,
            "OFF"
        )

        total += calculate_shift_hours(
            shift
        )

    return round(
        total,
        2
    )


# ============================================================
# DATABASE MIGRATION
# ============================================================

def migrate_database():

    """
    Safely adds missing location columns.

    Works with SQLite and PostgreSQL.
    """

    try:

        engine_name = db.engine.name

        required_columns = {
            "monday_location": "VARCHAR(200)",
            "tuesday_location": "VARCHAR(200)",
            "wednesday_location": "VARCHAR(200)",
            "thursday_location": "VARCHAR(200)",
            "friday_location": "VARCHAR(200)",
            "saturday_location": "VARCHAR(200)",
            "sunday_location": "VARCHAR(200)"
        }

        # ----------------------------------------------------
        # SQLITE
        # ----------------------------------------------------

        if engine_name == "sqlite":

            result = db.session.execute(
                db.text(
                    "PRAGMA table_info(roster)"
                )
            )

            existing_columns = {
                row[1]
                for row in result
            }

            for column, column_type in required_columns.items():

                if column not in existing_columns:

                    db.session.execute(
                        db.text(
                            f'ALTER TABLE roster '
                            f'ADD COLUMN "{column}" '
                            f'{column_type} DEFAULT ""'
                        )
                    )

            db.session.commit()

            print(
                "SQLite database migration completed."
            )

            return

        # ----------------------------------------------------
        # POSTGRESQL
        # ----------------------------------------------------

        if engine_name == "postgresql":

            for column, column_type in required_columns.items():

                db.session.execute(
                    db.text(
                        f'ALTER TABLE roster '
                        f'ADD COLUMN IF NOT EXISTS '
                        f'"{column}" '
                        f'{column_type} DEFAULT \'\''
                    )
                )

            db.session.commit()

            print(
                "PostgreSQL database migration completed."
            )

            return

        print(
            f"No migration required for database: {engine_name}"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "DATABASE MIGRATION ERROR:"
        )

        print(
            repr(exc)
        )


# ============================================================
# CLEAN OLD ROSTERS
# ============================================================

def clean_roster_dates():

    try:

        rosters = (
            Roster.query
            .order_by(
                Roster.id.asc()
            )
            .all()
        )

        seen = {}

        changed = False

        for roster in rosters:

            try:

                normalized = normalize_week_start(
                    roster.week_start
                )

            except ValueError:

                continue

            if roster.week_start != normalized:

                roster.week_start = normalized

                changed = True

            key = (
                roster.employee_id,
                normalized
            )

            if key in seen:

                old_roster = seen[key]

                if roster.id > old_roster.id:

                    db.session.delete(
                        old_roster
                    )

                    seen[key] = roster

                else:

                    db.session.delete(
                        roster
                    )

                changed = True

            else:

                seen[key] = roster

        if changed:

            db.session.commit()

    except Exception as exc:

        db.session.rollback()

        print(
            f"Roster cleanup error: {exc}"
        )


# ============================================================
# AUTH DECORATORS
# ============================================================

def admin_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if (
            not session.get("user_id")
            or session.get("role") != "admin"
        ):

            flash(
                "Admin access required.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return wrapper


def login_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return wrapper


# ============================================================
# TEMPLATE GLOBALS
# ============================================================

@app.context_processor
def inject_globals():

    return {
        "days": DAYS,
        "calculate_shift_hours":
            calculate_shift_hours,
        "calculate_weekly_hours":
            calculate_weekly_hours
    }


# ============================================================
# DEFAULT ADMIN
# ============================================================

def seed_admin():

    try:

        admin_email = "admin@roster.local"

        existing_admin = User.query.filter_by(
            email=admin_email
        ).first()

        if not existing_admin:

            admin = User(
                name="System Admin",
                email=admin_email,
                password_hash=generate_password_hash(
                    "admin123"
                ),
                role="admin",
                active=True
            )

            db.session.add(admin)

            db.session.commit()

            print(
                "Default admin created."
            )

    except Exception as exc:

        db.session.rollback()

        print(
            f"Admin seed error: {exc}"
        )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    if session.get("user_id"):

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        try:

            user = User.query.filter_by(
                email=email,
                active=True
            ).first()

        except Exception as exc:

            print(
                f"Login database error: {exc}"
            )

            flash(
                "Database error. Please try again.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        if user and check_password_hash(
            user.password_hash,
            password
        ):

            session.clear()

            session["user_id"] = user.id
            session["role"] = user.role
            session["name"] = user.name

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "admin":

        employees = (
            User.query
            .filter(
                User.role == "employee"
            )
            .order_by(
                User.name.asc()
            )
            .all()
        )

        roster_count = Roster.query.count()

        return render_template(
            "dashboard.html",
            employees=employees,
            roster_count=roster_count
        )

    employee = db.session.get(
        User,
        session["user_id"]
    )

    if not employee:

        session.clear()

        return redirect(
            url_for("login")
        )

    rosters = (
        Roster.query
        .filter_by(
            employee_id=employee.id
        )
        .order_by(
            Roster.week_start.desc()
        )
        .all()
    )

    return render_template(
        "employee_dashboard.html",
        employee=employee,
        rosters=rosters
    )


# ============================================================
# EMPLOYEES
# ============================================================

@app.route("/employees")
@admin_required
def employees():

    items = (
        User.query
        .filter(
            User.role == "employee"
        )
        .order_by(
            User.name.asc()
        )
        .all()
    )

    return render_template(
        "employees.html",
        employees=items
    )


# ============================================================
# ADD EMPLOYEE
# ============================================================

@app.route(
    "/employees/add",
    methods=["POST"]
)
@admin_required
def add_employee():

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    if not name or not email or not password:

        flash(
            "All fields are required.",
            "danger"
        )

        return redirect(
            url_for("employees")
        )

    existing = User.query.filter_by(
        email=email
    ).first()

    if existing:

        flash(
            "An account with this email already exists.",
            "warning"
        )

        return redirect(
            url_for("employees")
        )

    try:

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(
                password
            ),
            role="employee",
            active=True
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Employee added successfully.",
            "success"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            f"Add employee error: {repr(exc)}"
        )

        flash(
            "Could not add employee.",
            "danger"
        )

    return redirect(
        url_for("employees")
    )


# ============================================================
# DEACTIVATE EMPLOYEE
# ============================================================

@app.route(
    "/employees/<int:user_id>/deactivate",
    methods=["POST"]
)
@admin_required
def deactivate_employee(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user or user.role != "employee":

        flash(
            "Employee not found.",
            "danger"
        )

        return redirect(
            url_for("employees")
        )

    try:

        user.active = False

        db.session.commit()

        flash(
            f"{user.name} has been deactivated.",
            "warning"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            f"Deactivate employee error: {repr(exc)}"
        )

        flash(
            "Could not deactivate employee.",
            "danger"
        )

    return redirect(
        url_for("employees")
    )


# ============================================================
# ACTIVATE EMPLOYEE
# ============================================================

@app.route(
    "/employees/<int:user_id>/activate",
    methods=["POST"]
)
@admin_required
def activate_employee(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user or user.role != "employee":

        flash(
            "Employee not found.",
            "danger"
        )

        return redirect(
            url_for("employees")
        )

    try:

        user.active = True

        db.session.commit()

        flash(
            f"{user.name} has been activated.",
            "success"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            f"Activate employee error: {repr(exc)}"
        )

        flash(
            "Could not activate employee.",
            "danger"
        )

    return redirect(
        url_for("employees")
    )


# ============================================================
# DELETE EMPLOYEE
# ============================================================

@app.route(
    "/employees/<int:user_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_employee(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user or user.role != "employee":

        flash(
            "Employee not found.",
            "danger"
        )

        return redirect(
            url_for("employees")
        )

    try:

        db.session.delete(user)

        db.session.commit()

        flash(
            "Employee and all their roster history deleted.",
            "success"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            f"Delete employee error: {repr(exc)}"
        )

        flash(
            "Could not delete employee.",
            "danger"
        )

    return redirect(
        url_for("employees")
    )


# ============================================================
# EMPLOYEE HISTORY
# ============================================================

@app.route("/employee-history")
@admin_required
def employee_history():

    search = request.args.get(
        "search",
        ""
    ).strip()

    employees = []

    if search:

        employees = (
            User.query
            .filter(
                User.role == "employee",
                db.or_(
                    User.name.ilike(
                        f"%{search}%"
                    ),
                    User.email.ilike(
                        f"%{search}%"
                    )
                )
            )
            .order_by(
                User.name.asc()
            )
            .all()
        )

    selected_employee = None
    history = []

    total_weeks = 0
    total_worked_shifts = 0
    total_off_days = 0
    total_days_recorded = 0
    total_hours = 0

    first_week = None
    last_week = None

    employee_id = request.args.get(
        "employee_id",
        type=int
    )

    if employee_id:

        selected_employee = db.session.get(
            User,
            employee_id
        )

        if (
            selected_employee
            and selected_employee.role == "employee"
        ):

            history = (
                Roster.query
                .filter_by(
                    employee_id=selected_employee.id
                )
                .order_by(
                    Roster.week_start.asc()
                )
                .all()
            )

            total_weeks = len(history)

            if history:

                first_week = history[0].week_start
                last_week = history[-1].week_start

            for roster in history:

                total_hours += calculate_weekly_hours(
                    roster
                )

                for day in DAYS:

                    shift = getattr(
                        roster,
                        day,
                        "OFF"
                    )

                    total_days_recorded += 1

                    if (
                        shift
                        and str(shift).strip().upper() != "OFF"
                    ):

                        total_worked_shifts += 1

                    else:

                        total_off_days += 1

    return render_template(
        "employee_history.html",
        employees=employees,
        search=search,
        selected_employee=selected_employee,
        history=history,
        total_weeks=total_weeks,
        total_worked_shifts=total_worked_shifts,
        total_off_days=total_off_days,
        total_days_recorded=total_days_recorded,
        total_hours=round(
            total_hours,
            2
        ),
        first_week=first_week,
        last_week=last_week
    )


# ============================================================
# ROSTERS LIST
# ============================================================

@app.route("/rosters")
@admin_required
def rosters():

    data = (
        Roster.query
        .order_by(
            Roster.week_start.desc()
        )
        .all()
    )

    return render_template(
        "rosters.html",
        rosters=data
    )


# ============================================================
# CREATE / UPDATE ROSTER
# ============================================================

@app.route(
    "/rosters/create",
    methods=["GET", "POST"]
)
@admin_required
def create_roster():

    try:

        employees = (
            User.query
            .filter(
                User.role == "employee",
                User.active.is_(True)
            )
            .order_by(
                User.name.asc()
            )
            .all()
        )

    except Exception as exc:

        print(
            f"Employee loading error: {repr(exc)}"
        )

        flash(
            "Could not load employees.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return render_template(
            "create_roster.html",
            employees=employees
        )

    # ========================================================
    # POST
    # ========================================================

    print(
        "=========================================="
    )

    print(
        "CREATE ROSTER POST RECEIVED"
    )

    print(
        "FORM:",
        dict(request.form)
    )

    print(
        "=========================================="
    )

    employee_id = request.form.get(
        "employee_id",
        type=int
    )

    raw_week_start = request.form.get(
        "week_start",
        ""
    ).strip()

    # ========================================================
    # VALIDATION
    # ========================================================

    if not employee_id:

        flash(
            "Please select an employee.",
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    if not raw_week_start:

        flash(
            "Please select a week starting date.",
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    employee = db.session.get(
        User,
        employee_id
    )

    if not employee:

        flash(
            "Selected employee was not found.",
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    if employee.role != "employee":

        flash(
            "Selected user is not an employee.",
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    if not employee.active:

        flash(
            "Selected employee is inactive.",
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    # ========================================================
    # NORMALIZE DATE
    # ========================================================

    try:

        week_start = normalize_week_start(
            raw_week_start
        )

    except ValueError as exc:

        flash(
            str(exc),
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    # ========================================================
    # DATABASE SAVE
    # ========================================================

    try:

        roster = Roster.query.filter_by(
            employee_id=employee.id,
            week_start=week_start
        ).first()

        if roster:

            print(
                f"Updating existing roster ID: {roster.id}"
            )

        else:

            print(
                "Creating new roster..."
            )

            roster = Roster(
                employee_id=employee.id,
                week_start=week_start
            )

            db.session.add(roster)

        # ----------------------------------------------------
        # SAVE ALL DAYS
        # ----------------------------------------------------

        for day in DAYS:

            shift = request.form.get(
                day,
                "OFF"
            )

            location = request.form.get(
                f"{day}_location",
                ""
            )

            if shift is None:
                shift = "OFF"

            if location is None:
                location = ""

            shift = str(
                shift
            ).strip()

            location = str(
                location
            ).strip()

            setattr(
                roster,
                day,
                shift if shift else "OFF"
            )

            setattr(
                roster,
                f"{day}_location",
                location
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        db.session.commit()

        print(
            "ROSTER DATABASE SAVE SUCCESSFUL"
        )

        print(
            f"Employee: {employee.email}"
        )

        print(
            f"Week: {week_start}"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "=========================================="
        )

        print(
            "CREATE ROSTER DATABASE ERROR"
        )

        print(
            repr(exc)
        )

        print(
            "=========================================="
        )

        flash(
            f"Could not save roster: {exc}",
            "danger"
        )

        return redirect(
            url_for("create_roster")
        )

    # ========================================================
    # EMAIL
    # ========================================================

    shifts = {}
    locations = {}

    for day in DAYS:

        shifts[day] = getattr(
            roster,
            day,
            "OFF"
        )

        locations[day] = getattr(
            roster,
            f"{day}_location",
            ""
        )

    try:

        email_sent = send_roster_email(
            employee_name=employee.name,
            employee_email=employee.email,
            week_start=week_start,
            shifts=shifts,
            locations=locations
        )

    except Exception as exc:

        print(
            f"Email error: {repr(exc)}"
        )

        email_sent = False

    # ========================================================
    # RESULT
    # ========================================================

    if email_sent:

        flash(
            f"Roster saved and email sent to "
            f"{employee.email}.",
            "success"
        )

    else:

        flash(
            f"Roster saved successfully. "
            f"Email could not be sent to "
            f"{employee.email}.",
            "warning"
        )

    return redirect(
        url_for("rosters")
    )


# ============================================================
# DELETE ROSTER
# ============================================================

@app.route(
    "/rosters/<int:roster_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_roster(roster_id):

    roster = db.session.get(
        Roster,
        roster_id
    )

    if not roster:

        flash(
            "Roster not found.",
            "danger"
        )

        return redirect(
            url_for("rosters")
        )

    try:

        db.session.delete(
            roster
        )

        db.session.commit()

        flash(
            "Roster deleted.",
            "success"
        )

    except Exception as exc:

        db.session.rollback()

        print(
            f"Delete roster error: {repr(exc)}"
        )

        flash(
            "Could not delete roster.",
            "danger"
        )

    return redirect(
        url_for("rosters")
    )


# ============================================================
# VIEW ROSTER
# ============================================================

@app.route(
    "/roster/<int:roster_id>"
)
@login_required
def view_roster(roster_id):

    roster = db.session.get(
        Roster,
        roster_id
    )

    if not roster:

        flash(
            "Roster not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if (
        session.get("role") != "admin"
        and roster.employee_id != session.get("user_id")
    ):

        flash(
            "You are not allowed to view this roster.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "view_roster.html",
        roster=roster
    )


# ============================================================
# CSV UPLOAD
# ============================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
@admin_required
def upload_csv():

    if request.method == "GET":

        return render_template(
            "upload.html"
        )

    file = request.files.get(
        "file"
    )

    if (
        not file
        or not file.filename
        or not file.filename.lower().endswith(".csv")
    ):

        flash(
            "Please select a CSV file.",
            "danger"
        )

        return redirect(
            url_for("upload_csv")
        )

    try:

        text = file.read().decode(
            "utf-8-sig"
        )

        reader = csv.DictReader(
            io.StringIO(text)
        )

        required = {
            "name",
            "email",
            "week_start"
        }

        for day in DAYS:

            required.add(day)

            required.add(
                f"{day}_location"
            )

        headers = set(
            reader.fieldnames or []
        )

        if not required.issubset(headers):

            flash(
                "CSV columns are incorrect. "
                "Download the template first.",
                "danger"
            )

            return redirect(
                url_for("upload_csv")
            )

        created = 0
        emails_sent = 0
        emails_failed = 0

        for row in reader:

            name = row.get(
                "name",
                ""
            ).strip()

            email = row.get(
                "email",
                ""
            ).strip().lower()

            raw_week_start = row.get(
                "week_start",
                ""
            ).strip()

            if (
                not name
                or not email
                or not raw_week_start
            ):
                continue

            try:

                week_start = normalize_week_start(
                    raw_week_start
                )

            except ValueError:

                continue

            user = User.query.filter_by(
                email=email
            ).first()

            if not user:

                user = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(
                        "ChangeMe123!"
                    ),
                    role="employee",
                    active=True
                )

                db.session.add(user)

                db.session.flush()

            elif user.role != "employee":

                continue

            else:

                user.name = name

            roster = Roster.query.filter_by(
                employee_id=user.id,
                week_start=week_start
            ).first()

            if not roster:

                roster = Roster(
                    employee_id=user.id,
                    week_start=week_start
                )

                db.session.add(roster)

            for day in DAYS:

                shift = row.get(
                    day,
                    "OFF"
                )

                location = row.get(
                    f"{day}_location",
                    ""
                )

                shift = (
                    str(shift)
                    .strip()
                    if shift is not None
                    else "OFF"
                )

                location = (
                    str(location)
                    .strip()
                    if location is not None
                    else ""
                )

                setattr(
                    roster,
                    day,
                    shift or "OFF"
                )

                setattr(
                    roster,
                    f"{day}_location",
                    location
                )

            db.session.flush()

            shifts = {}
            locations = {}

            for day in DAYS:

                shifts[day] = getattr(
                    roster,
                    day,
                    "OFF"
                )

                locations[day] = getattr(
                    roster,
                    f"{day}_location",
                    ""
                )

            try:

                email_sent = send_roster_email(
                    employee_name=user.name,
                    employee_email=user.email,
                    week_start=week_start,
                    shifts=shifts,
                    locations=locations
                )

            except Exception as exc:

                print(
                    f"Email error for "
                    f"{user.email}: {repr(exc)}"
                )

                email_sent = False

            if email_sent:

                emails_sent += 1

            else:

                emails_failed += 1

            created += 1

        db.session.commit()

        flash(
            f"Imported {created} roster(s). "
            f"{emails_sent} email(s) sent successfully. "
            f"{emails_failed} email(s) failed.",
            "success"
        )

        return redirect(
            url_for("rosters")
        )

    except Exception as exc:

        db.session.rollback()

        print(
            f"CSV import error: {repr(exc)}"
        )

        flash(
            f"Could not import CSV: {exc}",
            "danger"
        )

        return redirect(
            url_for("upload_csv")
        )


# ============================================================
# CSV TEMPLATE DOWNLOAD
# ============================================================

@app.route("/template.csv")
@admin_required
def template_csv():

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    headers = [
        "name",
        "email",
        "week_start"
    ]

    for day in DAYS:

        headers.append(day)

        headers.append(
            f"{day}_location"
        )

    writer.writerow(
        headers
    )

    writer.writerow([
        "John Doe",
        "john@example.com",
        "2026-08-10",

        "08:00-16:00",
        "Dublin Office",

        "OFF",
        "",

        "16:00-00:00",
        "Dublin City Centre",

        "08:00-16:00",
        "Tallaght",

        "08:00-16:00",
        "Blanchardstown",

        "OFF",
        "",

        "OFF",
        ""
    ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=roster_template.csv"
        }
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    try:

        with app.app_context():

            db.create_all()

            print(
                "Database tables created/verified."
            )

            migrate_database()

            seed_admin()

            clean_roster_dates()

            print(
                "Database initialization completed."
            )

    except Exception as exc:

        print(
            "=========================================="
        )

        print(
            "DATABASE INITIALIZATION ERROR"
        )

        print(
            repr(exc)
        )

        print(
            "=========================================="
        )


initialize_database()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
