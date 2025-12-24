import datetime as dt
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("ADMIN", "TEACHER"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)

    teacher = db.relationship("User", foreign_keys=[teacher_id], lazy="joined")

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False, index=True)

    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum("M", "F"), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)

    classroom = db.relationship("Class", foreign_keys=[class_id], lazy="joined")

class HealthRecord(db.Model):
    __tablename__ = "health_records"
    __table_args__ = (
        db.UniqueConstraint("student_id", "record_date", name="uq_health_student_date"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    record_date = db.Column(db.Date, nullable=False, index=True)
    weight_kg = db.Column(db.Numeric(5, 2))
    temperature_c = db.Column(db.Numeric(4, 1), nullable=False)
    note = db.Column(db.String(255))

    student = db.relationship("Student", foreign_keys=[student_id], lazy="joined")

class MealLog(db.Model):
    __tablename__ = "meal_logs"
    __table_args__ = (
        db.UniqueConstraint("student_id", "log_date", name="uq_meal_student_date"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    log_date = db.Column(db.Date, nullable=False, index=True)
    ate = db.Column(db.Boolean, nullable=False, default=True)

    student = db.relationship("Student", foreign_keys=[student_id], lazy="joined")

class Invoice(db.Model):
    __tablename__ = "invoices"
    __table_args__ = (
        db.UniqueConstraint("student_id", "billing_month", name="uq_invoice_student_month"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    billing_month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    tuition_fee = db.Column(db.Integer, nullable=False)
    meal_unit_price = db.Column(db.Integer, nullable=False)
    meal_days = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("UNPAID", "PAID"), nullable=False, default="UNPAID")
    paid_at = db.Column(db.DateTime)
    collected_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))

    student = db.relationship("Student", foreign_keys=[student_id], lazy="joined")
    collector = db.relationship("User", foreign_keys=[collected_by], lazy="joined")

class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    tuition_fee_monthly = db.Column(db.Integer, nullable=False)
    meal_price_per_day = db.Column(db.Integer, nullable=False)
    max_students_per_class = db.Column(db.Integer, nullable=False)

    @staticmethod
    def get_current():
        return Settings.query.get(1)
