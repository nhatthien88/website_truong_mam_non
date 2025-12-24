import calendar
import datetime as dt
from io import BytesIO
from sqlalchemy import func
from flask import render_template, request, redirect, url_for, flash, send_file

from . import bp
from ..extensions import db
from ..models import Class, Student, Settings, HealthRecord, MealLog, Invoice
from ..utils import role_required
from flask_login import current_user

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_fonts():
    try:
        import os
        from flask import current_app
        font_dir = os.path.join(current_app.root_path, 'static', 'fonts')
        pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(font_dir, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(font_dir, 'DejaVuSans-Bold.ttf')))
        return 'DejaVuSans', 'DejaVuSans-Bold'
    except Exception as e:
        print(f"Font registration failed: {e}")
        return 'Helvetica', 'Helvetica-Bold'

def _get_teacher_class():
    return Class.query.filter_by(teacher_id=current_user.id).first()

def _month_range(yyyy_mm: str):
    year, month = map(int, yyyy_mm.split("-"))
    start = dt.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = dt.date(year, month, last_day)
    return start, end

@bp.route("/")
@role_required("TEACHER")
def dashboard():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    student_count = Student.query.filter_by(class_id=classroom.id).count()
    return render_template("teacher/dashboard.html", classroom=classroom, student_count=student_count)

@bp.route("/students")
@role_required("TEACHER")
def students_list():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    students = Student.query.filter_by(class_id=classroom.id).order_by(Student.id.desc()).all()
    settings = Settings.get_current()
    max_students = settings.max_students_per_class if settings else 25
    return render_template("teacher/students/list.html", classroom=classroom, students=students, max_students=max_students)

@bp.route("/students/create", methods=["GET", "POST"])
@role_required("TEACHER")
def students_create():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    settings = Settings.get_current()
    max_students = settings.max_students_per_class if settings else 25
    current_count = Student.query.filter_by(class_id=classroom.id).count()
    if request.method == "POST":
        if current_count >= max_students:
            flash(f"Lớp đã đủ {max_students} trẻ.", "danger")
            return redirect(url_for("teacher.students_list"))

        full_name = request.form.get("full_name", "").strip()
        dob = request.form.get("dob", "").strip()
        gender = request.form.get("gender", "").strip()
        parent_name = request.form.get("parent_name", "").strip()
        parent_phone = request.form.get("parent_phone", "").strip()

        if not all([full_name, dob, gender, parent_name, parent_phone]):
            flash("Vui lòng nhập đầy đủ thông tin.", "danger")
            return render_template("teacher/students/form.html", mode="create", classroom=classroom)

        try:
            dob_date = dt.datetime.strptime(dob, "%Y-%m-%d").date()
        except Exception:
            flash("Ngày sinh không hợp lệ.", "danger")
            return render_template("teacher/students/form.html", mode="create", classroom=classroom)

        st = Student(
            class_id=classroom.id,
            full_name=full_name,
            dob=dob_date,
            gender=gender,
            parent_name=parent_name,
            parent_phone=parent_phone
        )
        db.session.add(st)
        try:
            db.session.commit()
            flash("Thêm học sinh thành công.", "success")
            return redirect(url_for("teacher.students_list"))
        except Exception:
            db.session.rollback()
            flash("Không thể thêm học sinh.", "danger")

    return render_template("teacher/students/form.html", mode="create", classroom=classroom)

@bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@role_required("TEACHER")
def students_edit(student_id):
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    st = Student.query.get_or_404(student_id)
    if st.class_id != classroom.id:
        flash("Bạn không có quyền.", "danger")
        return redirect(url_for("teacher.students_list"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        dob = request.form.get("dob", "").strip()
        gender = request.form.get("gender", "").strip()
        parent_name = request.form.get("parent_name", "").strip()
        parent_phone = request.form.get("parent_phone", "").strip()

        if not all([full_name, dob, gender, parent_name, parent_phone]):
            flash("Vui lòng nhập đầy đủ thông tin.", "danger")
            return render_template("teacher/students/form.html", mode="edit", classroom=classroom, student=st)

        try:
            dob_date = dt.datetime.strptime(dob, "%Y-%m-%d").date()
        except Exception:
            flash("Ngày sinh không hợp lệ.", "danger")
            return render_template("teacher/students/form.html", mode="edit", classroom=classroom, student=st)

        st.full_name = full_name
        st.dob = dob_date
        st.gender = gender
        st.parent_name = parent_name
        st.parent_phone = parent_phone
        try:
            db.session.commit()
            flash("Cập nhật thành công.", "success")
            return redirect(url_for("teacher.students_list"))
        except Exception:
            db.session.rollback()
            flash("Không thể cập nhật.", "danger")

    return render_template("teacher/students/form.html", mode="edit", classroom=classroom, student=st)

@bp.route("/students/<int:student_id>/delete", methods=["POST"])
@role_required("TEACHER")
def students_delete(student_id):
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    st = Student.query.get_or_404(student_id)
    if st.class_id != classroom.id:
        flash("Bạn không có quyền.", "danger")
        return redirect(url_for("teacher.students_list"))

    try:
        db.session.delete(st)
        db.session.commit()
        flash("Đã xóa học sinh.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể xóa học sinh.", "danger")
    return redirect(url_for("teacher.students_list"))

@bp.route("/health")
@role_required("TEACHER")
def health_list():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    date_str = request.args.get("date")
    if date_str:
        try:
            record_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            record_date = dt.date.today()
    else:
        record_date = dt.date.today()

    students = Student.query.filter_by(class_id=classroom.id).order_by(Student.full_name).all()
    records = HealthRecord.query.filter(
        HealthRecord.record_date == record_date,
        HealthRecord.student_id.in_([s.id for s in students]) if students else False
    ).all()
    record_map = {r.student_id: r for r in records}

    return render_template("teacher/health/list.html",
                           classroom=classroom,
                           record_date=record_date,
                           students=students,
                           record_map=record_map)

@bp.route("/health/<int:student_id>/edit", methods=["GET", "POST"])
@role_required("TEACHER")
def health_edit(student_id):
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    st = Student.query.get_or_404(student_id)
    if st.class_id != classroom.id:
        flash("Bạn không có quyền.", "danger")
        return redirect(url_for("teacher.health_list"))

    date_str = request.args.get("date") or dt.date.today().strftime("%Y-%m-%d")
    try:
        record_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        record_date = dt.date.today()

    rec = HealthRecord.query.filter_by(student_id=st.id, record_date=record_date).first()

    if request.method == "POST":
        weight = request.form.get("weight_kg", "").strip() or None
        temp = request.form.get("temperature_c", "").strip()
        note = request.form.get("note", "").strip() or None

        try:
            weight_val = float(weight) if weight is not None else None
            temp_val = float(temp)
        except Exception:
            flash("Dữ liệu không hợp lệ.", "danger")
            return render_template("teacher/health/form.html", classroom=classroom, student=st, record_date=record_date, record=rec)

        if rec:
            rec.weight_kg = weight_val
            rec.temperature_c = temp_val
            rec.note = note
        else:
            rec = HealthRecord(student_id=st.id, record_date=record_date, weight_kg=weight_val, temperature_c=temp_val, note=note)
            db.session.add(rec)

        try:
            db.session.commit()
            flash("Lưu ghi nhận sức khỏe thành công.", "success")
        except Exception:
            db.session.rollback()
            flash("Không thể lưu ghi nhận.", "danger")

        return redirect(url_for("teacher.health_list", date=record_date.strftime("%Y-%m-%d")))

    return render_template("teacher/health/form.html", classroom=classroom, student=st, record_date=record_date, record=rec)

@bp.route("/meals", methods=["GET", "POST"])
@role_required("TEACHER")
def meals_daily():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    date_str = request.args.get("date")
    if date_str:
        try:
            log_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            log_date = dt.date.today()
    else:
        log_date = dt.date.today()

    students = Student.query.filter_by(class_id=classroom.id).order_by(Student.full_name).all()

    logs = MealLog.query.filter(
        MealLog.log_date == log_date,
        MealLog.student_id.in_([s.id for s in students]) if students else False
    ).all()
    log_map = {l.student_id: l for l in logs}

    billing_month = log_date.strftime("%Y-%m")
    student_ids = [s.id for s in students]
    paid_rows = (
        db.session.query(Invoice.student_id)
        .filter(
            Invoice.billing_month == billing_month,
            Invoice.status == "PAID",
            Invoice.student_id.in_(student_ids) if student_ids else False
        )
        .all()
    )
    locked_ids = {sid for (sid,) in paid_rows}


    if request.method == "POST":
        try:
            for st in students:
                if st.id in locked_ids:
                    continue
                ate = request.form.get(f"ate_{st.id}") == "1"
                ml = MealLog.query.filter_by(student_id=st.id, log_date=log_date).first()
                if ml:
                    ml.ate = ate
                else:
                    db.session.add(MealLog(student_id=st.id, log_date=log_date, ate=ate))
            db.session.commit()
            flash("Đã lưu ghi nhận ăn theo ngày.", "success")
        except Exception:
            db.session.rollback()
            flash("Không thể lưu dữ liệu.", "danger")

        return redirect(url_for("teacher.meals_daily", date=log_date.strftime("%Y-%m-%d")))

    return render_template("teacher/meals/list.html", classroom=classroom, log_date=log_date, students=students, log_map=log_map, locked_ids=locked_ids)

@bp.route("/tuition")
@role_required("TEACHER")
def tuition():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    month = request.args.get("month") or dt.date.today().strftime("%Y-%m")
    try:
        _month_range(month)
    except Exception:
        month = dt.date.today().strftime("%Y-%m")

    students = Student.query.filter_by(class_id=classroom.id).order_by(Student.full_name).all()
    settings = Settings.get_current()
    tuition_fee = settings.tuition_fee_monthly if settings else 1500000
    meal_price = settings.meal_price_per_day if settings else 25000

    start, end = _month_range(month)

    meal_counts = (
        db.session.query(MealLog.student_id, func.count(MealLog.id))
        .filter(
            MealLog.ate == True,
            MealLog.log_date >= start,
            MealLog.log_date <= end,
            MealLog.student_id.in_([s.id for s in students]) if students else False
        )
        .group_by(MealLog.student_id)
        .all()
    )
    meal_map = {sid: int(c) for sid, c in meal_counts}

    invoices = Invoice.query.filter(
        Invoice.billing_month == month,
        Invoice.student_id.in_([s.id for s in students]) if students else False
    ).all()
    inv_map = {inv.student_id: inv for inv in invoices}

    rows = []
    for st in students:
        inv = inv_map.get(st.id)

        if inv and inv.status == "PAID":
            meal_days = inv.meal_days
            tuition_val = inv.tuition_fee
            meal_price_val = inv.meal_unit_price
            total = inv.total_amount
        else:
            meal_days = meal_map.get(st.id, 0)
            tuition_val = tuition_fee
            meal_price_val = meal_price
            total = tuition_val + meal_days * meal_price_val

        rows.append({
            "student": st,
            "meal_days": meal_days,
            "tuition_fee": tuition_val,
            "meal_price": meal_price_val,
            "total": total,
            "invoice": inv
        })
    return render_template("teacher/tuition/list.html", classroom=classroom, month=month, rows=rows)

@bp.route("/tuition/<int:student_id>/generate", methods=["POST"])
@role_required("TEACHER")
def invoice_generate(student_id):
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    month = request.form.get("month") or dt.date.today().strftime("%Y-%m")
    st = Student.query.get_or_404(student_id)
    if st.class_id != classroom.id:
        flash("Bạn không có quyền.", "danger")
        return redirect(url_for("teacher.tuition", month=month))

    settings = Settings.get_current()
    tuition_fee = settings.tuition_fee_monthly if settings else 1500000
    meal_price = settings.meal_price_per_day if settings else 25000

    start, end = _month_range(month)
    meal_days = MealLog.query.filter(
        MealLog.student_id == st.id,
        MealLog.ate == True,
        MealLog.log_date >= start,
        MealLog.log_date <= end
    ).count()
    total = tuition_fee + meal_days * meal_price

    inv = Invoice.query.filter_by(student_id=st.id, billing_month=month).first()
    if inv and inv.status == "PAID":
        flash("Hóa đơn đã thu, không thể cập nhật.", "warning")
        return redirect(url_for("teacher.tuition", month=month))

    try:
        if inv:
            inv.tuition_fee = tuition_fee
            inv.meal_unit_price = meal_price
            inv.meal_days = meal_days
            inv.total_amount = total
        else:
            inv = Invoice(
                student_id=st.id,
                billing_month=month,
                tuition_fee=tuition_fee,
                meal_unit_price=meal_price,
                meal_days=meal_days,
                total_amount=total,
                status="UNPAID"
            )
            db.session.add(inv)

        db.session.commit()
        flash("Đã tạo/cập nhật hóa đơn.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể tạo hóa đơn.", "danger")

    return redirect(url_for("teacher.tuition", month=month))

@bp.route("/invoices/<int:invoice_id>")
@role_required("TEACHER")
def invoice_detail(invoice_id):
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    inv = Invoice.query.get_or_404(invoice_id)
    if inv.student.class_id != classroom.id:
        flash("Bạn không có quyền.", "danger")
        return redirect(url_for("teacher.tuition", month=inv.billing_month))

    return render_template("teacher/tuition/detail.html", classroom=classroom, inv=inv)

@bp.route("/invoices/<int:invoice_id>/confirm", methods=["POST"])
@role_required("TEACHER")
def invoice_confirm(invoice_id):
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    inv = Invoice.query.get_or_404(invoice_id)
    if inv.student.class_id != classroom.id:
        flash("Bạn không có quyền.", "danger")
        return redirect(url_for("teacher.tuition", month=inv.billing_month))

    if inv.status == "PAID":
        flash("Hóa đơn đã thu trước đó.", "info")
        return redirect(url_for("teacher.invoice_detail", invoice_id=inv.id))

    inv.status = "PAID"
    inv.paid_at = dt.datetime.now()
    inv.collected_by = current_user.id

    try:
        db.session.commit()
        flash("Đã xác nhận đã thu.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể xác nhận.", "danger")

    return redirect(url_for("teacher.invoice_detail", invoice_id=inv.id))

@bp.route("/reports")
@role_required("TEACHER")
def reports():
    classroom = _get_teacher_class()
    if not classroom:
        return render_template("teacher/no_class.html")

    month = request.args.get("month") or dt.date.today().strftime("%Y-%m")
    try:
        start, end = _month_range(month)
    except Exception:
        month = dt.date.today().strftime("%Y-%m")
        start, end = _month_range(month)

    students = Student.query.filter_by(class_id=classroom.id).all()
    student_count = len(students)

    gender_counts = (
        db.session.query(Student.gender, func.count(Student.id))
        .filter(Student.class_id == classroom.id)
        .group_by(Student.gender)
        .all()
    )
    gender = {"M": 0, "F": 0}
    for g, c in gender_counts:
        gender[g] = int(c)

    revenue = (
        db.session.query(func.sum(Invoice.total_amount))
        .join(Student, Student.id == Invoice.student_id)
        .filter(
            Student.class_id == classroom.id,
            Invoice.billing_month == month,
            Invoice.status == "PAID"
        )
        .scalar()
    )
    revenue = int(revenue or 0)

    invs = (
        Invoice.query
        .join(Student, Student.id == Invoice.student_id)
        .filter(Student.class_id == classroom.id, Invoice.billing_month == month)
        .order_by(Invoice.status, Student.full_name)
        .all()
    )

    return render_template("teacher/reports.html",
                           classroom=classroom,
                           month=month,
                           student_count=student_count,
                           gender=gender,
                           revenue=revenue,
                           invs=invs)

@bp.route("/reports/export-pdf")
@role_required("TEACHER")
def export_reports_pdf():
    classroom = _get_teacher_class()
    if not classroom:
        return redirect(url_for("teacher.dashboard"))

    month = request.args.get("month") or dt.date.today().strftime("%Y-%m")
    try:
        start, end = _month_range(month)
    except Exception:
        month = dt.date.today().strftime("%Y-%m")
        start, end = _month_range(month)

    students = Student.query.filter_by(class_id=classroom.id).all()
    student_count = len(students)

    gender_counts = (
        db.session.query(Student.gender, func.count(Student.id))
        .filter(Student.class_id == classroom.id)
        .group_by(Student.gender)
        .all()
    )
    gender = {"M": 0, "F": 0}
    for g, c in gender_counts:
        gender[g] = int(c)

    revenue = (
        db.session.query(func.sum(Invoice.total_amount))
        .join(Student, Student.id == Invoice.student_id)
        .filter(
            Student.class_id == classroom.id,
            Invoice.billing_month == month,
            Invoice.status == "PAID"
        )
        .scalar()
    )
    revenue = int(revenue or 0)

    invs = (
        Invoice.query
        .join(Student, Student.id == Invoice.student_id)
        .filter(Student.class_id == classroom.id, Invoice.billing_month == month)
        .order_by(Invoice.status, Student.full_name)
        .all()
    )
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    font_name, font_bold = register_fonts()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName=font_bold
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=20,
        fontName=font_bold
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10
    )
    
    elements.append(Paragraph(f"BÁO CÁO THÁNG {month}", title_style))
    elements.append(Paragraph(f"Lớp: {classroom.name}", normal_style))
    elements.append(Paragraph(f"Giáo viên: {current_user.full_name}", normal_style))
    elements.append(Paragraph(f"Ngày xuất: {dt.date.today().strftime('%d/%m/%Y')}", normal_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("TỔNG QUAN LỚP HỌC", heading_style))
    overview_data = [
        ['Chỉ tiêu', 'Giá trị'],
        ['Sĩ số lớp', str(student_count)],
        ['Số học sinh nam', str(gender['M'])],
        ['Số học sinh nữ', str(gender['F'])],
        [f'Doanh thu tháng {month}', f"{revenue:,} VND"],
    ]
    overview_table = Table(overview_data, colWidths=[10*cm, 6*cm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph(f"HÓA ĐƠN THÁNG {month}", heading_style))
    invoice_data = [['Học sinh', 'Tổng tiền (VND)', 'Trạng thái', 'Ngày thu']]
    for inv in invs:
        status = "Đã thu" if inv.status == "PAID" else "Chưa thu"
        paid_date = inv.paid_at.strftime('%d/%m/%Y %H:%M') if inv.paid_at else '-'
        invoice_data.append([
            inv.student.full_name,
            f"{inv.total_amount:,}",
            status,
            paid_date
        ])
    
    invoice_table = Table(invoice_data, colWidths=[5*cm, 4*cm, 3*cm, 4*cm])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(invoice_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'bao_cao_{classroom.name}_{month}.pdf'
    )
