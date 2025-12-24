import datetime as dt

from app import create_app
from app.extensions import db
from app.models import User, Class, Student, Settings, MealLog, HealthRecord, Invoice

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        settings = Settings.query.get(1)
        if not settings:
            settings = Settings(
                id=1,
                tuition_fee_monthly=1500000,
                meal_price_per_day=25000,
                max_students_per_class=25
            )
            db.session.add(settings)
            db.session.commit()

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", role="ADMIN", full_name="Administrator", phone="0900000000")
            admin.set_password("admin")
            db.session.add(admin)
            db.session.commit()

        teacher = User.query.filter_by(username="teacher1").first()
        if not teacher:
            teacher = User(username="teacher1", role="TEACHER", full_name="Teacher One", phone="0911111111")
            teacher.set_password("admin")
            db.session.add(teacher)
            db.session.commit()

        classroom = Class.query.filter_by(teacher_id=teacher.id).first()
        if not classroom:
            classroom = Class.query.filter_by(teacher_id=None).first()
            if classroom:
                classroom.teacher_id = teacher.id
            else:
                classroom = Class(name="Lá 1", teacher_id=teacher.id)
                db.session.add(classroom)
            db.session.commit()

        if Student.query.filter_by(class_id=classroom.id).count() == 0:
            s1 = Student(
                class_id=classroom.id,
                full_name="Nguyễn Gia Hân",
                dob=dt.date(2020, 8, 10),
                gender="F",
                parent_name="Nguyễn Triều Nguyệt",
                parent_phone="0965544789"
            )
            s2 = Student(
                class_id=classroom.id,
                full_name="Trần Minh Khang",
                dob=dt.date(2020, 3, 5),
                gender="M",
                parent_name="Trần Thị Hoa",
                parent_phone="0901234567"
            )
            db.session.add_all([s1, s2])
            db.session.commit()

        today = dt.date.today()
        start_month = today.replace(day=1)
        students = Student.query.filter_by(class_id=classroom.id).all()
        for i in range(5):
            d = start_month + dt.timedelta(days=i)
            for st in students:
                if not MealLog.query.filter_by(student_id=st.id, log_date=d).first():
                    db.session.add(MealLog(student_id=st.id, log_date=d, ate=True))
        db.session.commit()

        first = students[0]
        if not HealthRecord.query.filter_by(student_id=first.id, record_date=today).first():
            db.session.add(HealthRecord(
                student_id=first.id,
                record_date=today,
                weight_kg=15.0,
                temperature_c=36.8,
                note="Bình thường"
            ))
            db.session.commit()

        billing_month = today.strftime("%Y-%m")
        inv = Invoice.query.filter_by(student_id=first.id, billing_month=billing_month).first()
        if not inv:
            end_month = (start_month.replace(day=28) + dt.timedelta(days=4))
            end_month = end_month - dt.timedelta(days=end_month.day)
            meal_days = MealLog.query.filter(
                MealLog.student_id==first.id,
                MealLog.ate==True,
                MealLog.log_date>=start_month,
                MealLog.log_date<=end_month
            ).count()
            tuition = settings.tuition_fee_monthly
            meal_price = settings.meal_price_per_day
            total = tuition + meal_days * meal_price
            inv = Invoice(
                student_id=first.id,
                billing_month=billing_month,
                tuition_fee=tuition,
                meal_unit_price=meal_price,
                meal_days=meal_days,
                total_amount=total,
                status="UNPAID",
                paid_at=None,
                collected_by=None
            )
            db.session.add(inv)
            db.session.commit()

        print("Seed done.")
        print("Admin: admin/admin")
        print("Teacher: teacher1/admin")

if __name__ == "__main__":
    seed()
