"""
Student Placement Management System - Backend
Flask + SQLAlchemy + SQLite REST API
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
import re
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)  # Allow frontend (different origin) to call this API

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'placement.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------
# MODELS
# --------------------------------------------------------------------------

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    branch = db.Column(db.String(80), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    placements = db.relationship("Placement", backref="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "roll_number": self.roll_number,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "branch": self.branch,
            "cgpa": self.cgpa,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(120), nullable=False)
    package_lpa = db.Column(db.Float, nullable=False)
    eligibility_cgpa = db.Column(db.Float, nullable=False, default=0)
    drive_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    placements = db.relationship("Placement", backref="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "package_lpa": self.package_lpa,
            "eligibility_cgpa": self.eligibility_cgpa,
            "drive_date": self.drive_date.isoformat() if self.drive_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Placement(db.Model):
    __tablename__ = "placements"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Applied")  # Applied, Shortlisted, Selected, Rejected
    package_offered = db.Column(db.Float)
    placement_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "status": self.status,
            "package_offered": self.package_offered,
            "placement_date": self.placement_date.isoformat() if self.placement_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


VALID_STATUSES = {"Applied", "Shortlisted", "Selected", "Rejected"}


# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------

def error(message, code=400):
    return jsonify({"error": message}), code


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format '{value}', expected YYYY-MM-DD")


# --------------------------------------------------------------------------
# ROOT / HEALTH
# --------------------------------------------------------------------------

@app.route("/")
def index():
    return jsonify({
        "message": "Student Placement Management System API",
        "status": "running",
        "endpoints": {
            "students": "/api/students/",
            "companies": "/api/companies/",
            "placements": "/api/placements/",
            "dashboard": "/api/dashboard/"
        }
    })


# --------------------------------------------------------------------------
# STUDENTS CRUD
# --------------------------------------------------------------------------

@app.route("/api/students/", methods=["GET"])
def get_students():
    search = request.args.get("search", "").strip()
    branch = request.args.get("branch", "").strip()
    query = Student.query
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Student.name.ilike(like), Student.roll_number.ilike(like), Student.email.ilike(like)))
    if branch:
        query = query.filter(Student.branch == branch)
    students = query.order_by(Student.id.desc()).all()
    return jsonify([s.to_dict() for s in students])


@app.route("/api/students/<int:student_id>/", methods=["GET"])
def get_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return error("Student not found", 404)
    return jsonify(student.to_dict())


@app.route("/api/students/", methods=["POST"])
def create_student():
    data = request.get_json(silent=True) or {}

    required = ["roll_number", "name", "email", "branch", "cgpa"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}")

    if not EMAIL_REGEX.match(data["email"]):
        return error("Invalid email format")

    try:
        cgpa = float(data["cgpa"])
    except (TypeError, ValueError):
        return error("CGPA must be a number")
    if not (0 <= cgpa <= 10):
        return error("CGPA must be between 0 and 10")

    if Student.query.filter_by(roll_number=data["roll_number"]).first():
        return error("A student with this roll number already exists", 409)
    if Student.query.filter_by(email=data["email"]).first():
        return error("A student with this email already exists", 409)

    student = Student(
        roll_number=data["roll_number"].strip(),
        name=data["name"].strip(),
        email=data["email"].strip(),
        phone=str(data.get("phone", "")).strip() or None,
        branch=data["branch"].strip(),
        cgpa=cgpa,
    )
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201


@app.route("/api/students/<int:student_id>/", methods=["PUT", "PATCH"])
def update_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return error("Student not found", 404)

    data = request.get_json(silent=True) or {}

    if "email" in data and data["email"]:
        if not EMAIL_REGEX.match(data["email"]):
            return error("Invalid email format")
        existing = Student.query.filter_by(email=data["email"]).first()
        if existing and existing.id != student_id:
            return error("A student with this email already exists", 409)
        student.email = data["email"].strip()

    if "roll_number" in data and data["roll_number"]:
        existing = Student.query.filter_by(roll_number=data["roll_number"]).first()
        if existing and existing.id != student_id:
            return error("A student with this roll number already exists", 409)
        student.roll_number = data["roll_number"].strip()

    if "cgpa" in data and data["cgpa"] is not None:
        try:
            cgpa = float(data["cgpa"])
        except (TypeError, ValueError):
            return error("CGPA must be a number")
        if not (0 <= cgpa <= 10):
            return error("CGPA must be between 0 and 10")
        student.cgpa = cgpa

    if "name" in data and data["name"]:
        student.name = data["name"].strip()
    if "phone" in data:
        student.phone = str(data.get("phone", "")).strip() or None
    if "branch" in data and data["branch"]:
        student.branch = data["branch"].strip()

    db.session.commit()
    return jsonify(student.to_dict())


@app.route("/api/students/<int:student_id>/", methods=["DELETE"])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return error("Student not found", 404)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted successfully"})


# --------------------------------------------------------------------------
# COMPANIES CRUD
# --------------------------------------------------------------------------

@app.route("/api/companies/", methods=["GET"])
def get_companies():
    search = request.args.get("search", "").strip()
    query = Company.query
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Company.name.ilike(like), Company.role.ilike(like)))
    companies = query.order_by(Company.id.desc()).all()
    return jsonify([c.to_dict() for c in companies])


@app.route("/api/companies/<int:company_id>/", methods=["GET"])
def get_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return error("Company not found", 404)
    return jsonify(company.to_dict())


@app.route("/api/companies/", methods=["POST"])
def create_company():
    data = request.get_json(silent=True) or {}

    required = ["name", "role", "package_lpa"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}")

    try:
        package_lpa = float(data["package_lpa"])
        if package_lpa < 0:
            raise ValueError()
    except (TypeError, ValueError):
        return error("package_lpa must be a positive number")

    eligibility_cgpa = data.get("eligibility_cgpa", 0)
    try:
        eligibility_cgpa = float(eligibility_cgpa) if eligibility_cgpa not in (None, "") else 0
    except (TypeError, ValueError):
        return error("eligibility_cgpa must be a number")

    try:
        drive_date = parse_date(data.get("drive_date"))
    except ValueError as e:
        return error(str(e))

    if Company.query.filter_by(name=data["name"]).first():
        return error("A company with this name already exists", 409)

    company = Company(
        name=data["name"].strip(),
        role=data["role"].strip(),
        package_lpa=package_lpa,
        eligibility_cgpa=eligibility_cgpa,
        drive_date=drive_date,
    )
    db.session.add(company)
    db.session.commit()
    return jsonify(company.to_dict()), 201


@app.route("/api/companies/<int:company_id>/", methods=["PUT", "PATCH"])
def update_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return error("Company not found", 404)

    data = request.get_json(silent=True) or {}

    if "name" in data and data["name"]:
        existing = Company.query.filter_by(name=data["name"]).first()
        if existing and existing.id != company_id:
            return error("A company with this name already exists", 409)
        company.name = data["name"].strip()
    if "role" in data and data["role"]:
        company.role = data["role"].strip()
    if "package_lpa" in data and data["package_lpa"] is not None:
        try:
            package_lpa = float(data["package_lpa"])
            if package_lpa < 0:
                raise ValueError()
        except (TypeError, ValueError):
            return error("package_lpa must be a positive number")
        company.package_lpa = package_lpa
    if "eligibility_cgpa" in data and data["eligibility_cgpa"] not in (None, ""):
        try:
            company.eligibility_cgpa = float(data["eligibility_cgpa"])
        except (TypeError, ValueError):
            return error("eligibility_cgpa must be a number")
    if "drive_date" in data:
        try:
            company.drive_date = parse_date(data.get("drive_date"))
        except ValueError as e:
            return error(str(e))

    db.session.commit()
    return jsonify(company.to_dict())


@app.route("/api/companies/<int:company_id>/", methods=["DELETE"])
def delete_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return error("Company not found", 404)
    db.session.delete(company)
    db.session.commit()
    return jsonify({"message": "Company deleted successfully"})


# --------------------------------------------------------------------------
# PLACEMENTS CRUD (links student <-> company)
# --------------------------------------------------------------------------

@app.route("/api/placements/", methods=["GET"])
def get_placements():
    status = request.args.get("status", "").strip()
    query = Placement.query
    if status:
        query = query.filter(Placement.status == status)
    placements = query.order_by(Placement.id.desc()).all()
    return jsonify([p.to_dict() for p in placements])


@app.route("/api/placements/<int:placement_id>/", methods=["GET"])
def get_placement(placement_id):
    placement = Placement.query.get(placement_id)
    if not placement:
        return error("Placement record not found", 404)
    return jsonify(placement.to_dict())


@app.route("/api/placements/", methods=["POST"])
def create_placement():
    data = request.get_json(silent=True) or {}

    required = ["student_id", "company_id"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}")

    student = Student.query.get(data["student_id"])
    if not student:
        return error("Student not found", 404)
    company = Company.query.get(data["company_id"])
    if not company:
        return error("Company not found", 404)

    status = data.get("status", "Applied")
    if status not in VALID_STATUSES:
        return error(f"status must be one of {sorted(VALID_STATUSES)}")

    package_offered = data.get("package_offered")
    if package_offered not in (None, ""):
        try:
            package_offered = float(package_offered)
        except (TypeError, ValueError):
            return error("package_offered must be a number")
    else:
        package_offered = None

    try:
        placement_date = parse_date(data.get("placement_date"))
    except ValueError as e:
        return error(str(e))

    placement = Placement(
        student_id=student.id,
        company_id=company.id,
        status=status,
        package_offered=package_offered,
        placement_date=placement_date,
    )
    db.session.add(placement)
    db.session.commit()
    return jsonify(placement.to_dict()), 201


@app.route("/api/placements/<int:placement_id>/", methods=["PUT", "PATCH"])
def update_placement(placement_id):
    placement = Placement.query.get(placement_id)
    if not placement:
        return error("Placement record not found", 404)

    data = request.get_json(silent=True) or {}

    if "student_id" in data and data["student_id"]:
        student = Student.query.get(data["student_id"])
        if not student:
            return error("Student not found", 404)
        placement.student_id = student.id

    if "company_id" in data and data["company_id"]:
        company = Company.query.get(data["company_id"])
        if not company:
            return error("Company not found", 404)
        placement.company_id = company.id

    if "status" in data and data["status"]:
        if data["status"] not in VALID_STATUSES:
            return error(f"status must be one of {sorted(VALID_STATUSES)}")
        placement.status = data["status"]

    if "package_offered" in data:
        if data["package_offered"] in (None, ""):
            placement.package_offered = None
        else:
            try:
                placement.package_offered = float(data["package_offered"])
            except (TypeError, ValueError):
                return error("package_offered must be a number")

    if "placement_date" in data:
        try:
            placement.placement_date = parse_date(data.get("placement_date"))
        except ValueError as e:
            return error(str(e))

    db.session.commit()
    return jsonify(placement.to_dict())


@app.route("/api/placements/<int:placement_id>/", methods=["DELETE"])
def delete_placement(placement_id):
    placement = Placement.query.get(placement_id)
    if not placement:
        return error("Placement record not found", 404)
    db.session.delete(placement)
    db.session.commit()
    return jsonify({"message": "Placement record deleted successfully"})


# --------------------------------------------------------------------------
# DASHBOARD / STATS
# --------------------------------------------------------------------------

@app.route("/api/dashboard/", methods=["GET"])
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_placements = Placement.query.count()
    selected = Placement.query.filter_by(status="Selected").count()
    packages = [p.package_offered for p in Placement.query.filter_by(status="Selected").all() if p.package_offered]
    avg_package = round(sum(packages) / len(packages), 2) if packages else 0
    highest_package = max(packages) if packages else 0

    return jsonify({
        "total_students": total_students,
        "total_companies": total_companies,
        "total_placements": total_placements,
        "students_selected": selected,
        "placement_percentage": round((selected / total_students) * 100, 2) if total_students else 0,
        "average_package_lpa": avg_package,
        "highest_package_lpa": highest_package,
    })


# --------------------------------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# --------------------------------------------------------------------------
# SAMPLE DATA SEEDING (only runs if database is empty)
# --------------------------------------------------------------------------

def seed_sample_data():
    if Student.query.first() is not None:
        return

    students = [
        Student(roll_number="CS001", name="Aarav Sharma", email="aarav.sharma@example.com", phone="9876543210", branch="Computer Science", cgpa=8.7),
        Student(roll_number="CS002", name="Diya Patel", email="diya.patel@example.com", phone="9876543211", branch="Computer Science", cgpa=9.1),
        Student(roll_number="EC001", name="Rohan Mehta", email="rohan.mehta@example.com", phone="9876543212", branch="Electronics", cgpa=7.8),
        Student(roll_number="ME001", name="Ishaan Verma", email="ishaan.verma@example.com", phone="9876543213", branch="Mechanical", cgpa=7.2),
        Student(roll_number="CS003", name="Ananya Iyer", email="ananya.iyer@example.com", phone="9876543214", branch="Computer Science", cgpa=8.3),
    ]
    db.session.add_all(students)

    companies = [
        Company(name="TechNova Solutions", role="Software Engineer", package_lpa=12.0, eligibility_cgpa=7.5, drive_date=date(2026, 8, 10)),
        Company(name="DataSphere Inc", role="Data Analyst", package_lpa=9.5, eligibility_cgpa=7.0, drive_date=date(2026, 8, 20)),
        Company(name="Quantum Systems", role="Backend Developer", package_lpa=15.0, eligibility_cgpa=8.0, drive_date=date(2026, 9, 1)),
    ]
    db.session.add_all(companies)
    db.session.commit()

    placements = [
        Placement(student_id=students[0].id, company_id=companies[0].id, status="Selected", package_offered=12.0, placement_date=date(2026, 8, 12)),
        Placement(student_id=students[1].id, company_id=companies[2].id, status="Selected", package_offered=15.0, placement_date=date(2026, 9, 3)),
        Placement(student_id=students[2].id, company_id=companies[1].id, status="Shortlisted"),
        Placement(student_id=students[4].id, company_id=companies[0].id, status="Applied"),
    ]
    db.session.add_all(placements)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_sample_data()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
