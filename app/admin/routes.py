import calendar
import datetime as dt
from io import BytesIO
from sqlalchemy import func
from flask import render_template, request, redirect, url_for, flash, send_file

from . import bp
from ..extensions import db
from ..models import User, Class, Student, Settings, Invoice
from ..utils import role_required

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

@bp.route("/")
@role_required("ADMIN")
def dashboard():
    class_count = Class.query.count()
    student_count = Student.query.count()
    teacher_count = User.query.filter_by(role="TEACHER").count()
    return render_template("admin/dashboard.html",
                           class_count=class_count,
                           student_count=student_count,
                           teacher_count=teacher_count)

@bp.route("/classes")
@role_required("ADMIN")
def classes_list():
    classes = Class.query.order_by(Class.id.desc()).all()
    assigned_teacher_ids = [c.teacher_id for c in classes if c.teacher_id is not None]
    teachers = User.query.filter_by(role="TEACHER")\
        .filter(~User.id.in_(assigned_teacher_ids))\
        .order_by(User.full_name).all()
    all_teachers = User.query.filter_by(role="TEACHER").order_by(User.full_name).all()
    return render_template("admin/classes/list.html", 
                          classes=classes, 
                          teachers=teachers,
                          all_teachers=all_teachers)

@bp.route("/classes/create", methods=["POST"])
@role_required("ADMIN")
def classes_create():
    name = request.form.get("name", "").strip()
    teacher_id = request.form.get("teacher_id") or None

    if not name:
        flash("Tên lớp không được để trống.", "danger")
        return redirect(url_for("admin.classes_list"))

    if teacher_id:
        teacher = User.query.filter_by(id=int(teacher_id), role="TEACHER").first()
        if not teacher:
            flash("Giáo viên không hợp lệ.", "danger")
            return redirect(url_for("admin.classes_list"))

        if Class.query.filter_by(teacher_id=teacher.id).first():
            flash("Giáo viên này đã được phân công lớp khác.", "danger")
            return redirect(url_for("admin.classes_list"))

    classroom = Class(name=name, teacher_id=int(teacher_id) if teacher_id else None)
    db.session.add(classroom)
    try:
        db.session.commit()
        flash("Tạo lớp thành công.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể tạo lớp (có thể trùng giáo viên phụ trách).", "danger")
    return redirect(url_for("admin.classes_list"))

@bp.route("/classes/<int:class_id>/edit", methods=["POST"])
@role_required("ADMIN")
def classes_edit(class_id):
    classroom = Class.query.get_or_404(class_id)
    name = request.form.get("name", "").strip()
    teacher_id = request.form.get("teacher_id") or None

    if not name:
        flash("Tên lớp không được để trống.", "danger")
        return redirect(url_for("admin.classes_list"))

    if teacher_id:
        teacher = User.query.filter_by(id=int(teacher_id), role="TEACHER").first()
        if not teacher:
            flash("Giáo viên không hợp lệ.", "danger")
            return redirect(url_for("admin.classes_list"))

        other_class = Class.query.filter(Class.teacher_id==teacher.id, Class.id!=classroom.id).first()
        if other_class:
            flash("Giáo viên này đã được phân công lớp khác.", "danger")
            return redirect(url_for("admin.classes_list"))

        classroom.teacher_id = teacher.id
    else:
        classroom.teacher_id = None

    classroom.name = name
    try:
        db.session.commit()
        flash("Cập nhật lớp thành công.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể cập nhật lớp.", "danger")

    return redirect(url_for("admin.classes_list"))

@bp.route("/classes/<int:class_id>/delete", methods=["POST"])
@role_required("ADMIN")
def classes_delete(class_id):
    classroom = Class.query.get_or_404(class_id)
    try:
        db.session.delete(classroom)
        db.session.commit()
        flash("Xóa lớp thành công.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể xóa lớp (có thể lớp vẫn còn học sinh).", "danger")
    return redirect(url_for("admin.classes_list"))

@bp.route("/teachers")
@role_required("ADMIN")
def teachers_list():
    teachers = User.query.filter_by(role="TEACHER").order_by(User.id.desc()).all()
    classes_unassigned = Class.query.filter_by(teacher_id=None).order_by(Class.name).all()
    all_classes = Class.query.all()
    return render_template("admin/teachers/list.html",
                           teachers=teachers,
                           classes_unassigned=classes_unassigned,
                           all_classes=all_classes)

@bp.route("/teachers/create", methods=["POST"])
@role_required("ADMIN")
def teachers_create():
    username = request.form.get("username", "").strip()
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip() or None
    password = request.form.get("password", "").strip()
    class_id = request.form.get("class_id") or None

    if not username or not full_name or not password:
        flash("Vui lòng nhập đầy đủ username, họ tên, mật khẩu.", "danger")
        return redirect(url_for("admin.teachers_list"))

    if User.query.filter_by(username=username).first():
        flash("Username đã tồn tại.", "danger")
        return redirect(url_for("admin.teachers_list"))

    teacher = User(username=username, role="TEACHER", full_name=full_name, phone=phone)
    teacher.set_password(password)
    db.session.add(teacher)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Không thể tạo tài khoản giáo viên.", "danger")
        return redirect(url_for("admin.teachers_list"))

    if class_id:
        classroom = Class.query.get(int(class_id))
        if classroom and classroom.teacher_id is None:
            classroom.teacher_id = teacher.id
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("Tạo tài khoản OK nhưng không thể phân công lớp.", "warning")

    flash("Tạo tài khoản giáo viên thành công.", "success")
    return redirect(url_for("admin.teachers_list"))

@bp.route("/teachers/<int:teacher_id>/edit", methods=["POST"])
@role_required("ADMIN")
def teachers_edit(teacher_id):
    teacher = User.query.filter_by(id=teacher_id, role="TEACHER").first_or_404()
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip() or None
    new_password = request.form.get("password", "").strip()
    class_id = request.form.get("class_id") or None

    if not full_name:
        flash("Họ tên không được để trống.", "danger")
        return redirect(url_for("admin.teachers_list"))

    teacher.full_name = full_name
    teacher.phone = phone
    if new_password:
        teacher.set_password(new_password)

    old_class = Class.query.filter_by(teacher_id=teacher.id).first()
    if old_class:
        old_class.teacher_id = None

    if class_id:
        classroom = Class.query.get(int(class_id))
        if classroom and classroom.teacher_id is None:
            classroom.teacher_id = teacher.id
        else:
            flash("Lớp không hợp lệ hoặc đã có giáo viên.", "danger")
            db.session.rollback()
            return redirect(url_for("admin.teachers_list"))

    try:
        db.session.commit()
        flash("Cập nhật giáo viên thành công.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể cập nhật giáo viên.", "danger")

    return redirect(url_for("admin.teachers_list"))

@bp.route("/teachers/<int:teacher_id>/delete", methods=["POST"])
@role_required("ADMIN")
def teachers_delete(teacher_id):
    teacher = User.query.filter_by(id=teacher_id, role="TEACHER").first_or_404()
    try:
        db.session.delete(teacher)
        db.session.commit()
        flash("Xóa tài khoản giáo viên thành công.", "success")
    except Exception:
        db.session.rollback()
        flash("Không thể xóa tài khoản.", "danger")
    return redirect(url_for("admin.teachers_list"))

@bp.route("/settings", methods=["GET", "POST"])
@role_required("ADMIN")
def settings_page():
    settings = Settings.get_current()
    if not settings:
        settings = Settings(id=1, tuition_fee_monthly=1500000, meal_price_per_day=25000, max_students_per_class=25)
        db.session.add(settings)
        db.session.commit()

    if request.method == "POST":
        form_type = request.form.get("form_type", "")
        
        try:
            if form_type == "tuition":
                tuition = int(request.form.get("tuition_fee_monthly", "0"))
                meal = int(request.form.get("meal_price_per_day", "0"))
                
                if tuition <= 0 or meal < 0:
                    raise ValueError()
                
                settings.tuition_fee_monthly = tuition
                settings.meal_price_per_day = meal
                db.session.commit()
                flash("Cập nhật học phí thành công.", "success")
                
            elif form_type == "capacity":
                max_st = int(request.form.get("max_students_per_class", "0"))
                
                if max_st <= 0:
                    raise ValueError()
                
                settings.max_students_per_class = max_st
                db.session.commit()
                flash("Cập nhật số lượng trẻ tối đa thành công.", "success")
            else:
                flash("Yêu cầu không hợp lệ.", "danger")
        except ValueError:
            db.session.rollback()
            flash("Dữ liệu không hợp lệ.", "danger")
        except Exception:
            db.session.rollback()
            flash("Không thể cập nhật quy định.", "danger")

        return redirect(url_for("admin.settings_page"))

    return render_template("admin/settings.html", settings=settings)

@bp.route("/reports")
@role_required("ADMIN")
def reports():
    total_students = Student.query.count()
    total_classes = Class.query.count()
    
    current_month = dt.date.today().strftime('%Y-%m')
    current_month_revenue = db.session.query(func.sum(Invoice.total_amount))\
        .filter(Invoice.status == "PAID", Invoice.billing_month == current_month)\
        .scalar() or 0
    
    class_sizes = (
        db.session.query(Class.id, Class.name, func.count(Student.id).label("student_count"))
        .outerjoin(Student, Student.class_id == Class.id)
        .group_by(Class.id, Class.name)
        .order_by(Class.name)
        .all()
    )

    gender_counts = (
        db.session.query(Student.gender, func.count(Student.id))
        .group_by(Student.gender)
        .all()
    )
    gender = {"M": 0, "F": 0}
    for g, c in gender_counts:
        gender[g] = int(c)

    revenue_rows = (
        db.session.query(Invoice.billing_month, func.sum(Invoice.total_amount))
        .filter(Invoice.status == "PAID")
        .group_by(Invoice.billing_month)
        .order_by(Invoice.billing_month.desc())
        .all()
    )
    revenue = [{"month": m, "total": int(t or 0)} for m, t in revenue_rows]

    return render_template("admin/reports.html",
                           total_students=total_students,
                           total_classes=total_classes,
                           current_month_revenue=int(current_month_revenue),
                           class_sizes=class_sizes,
                           revenue=revenue,
                           gender=gender)

@bp.route("/reports/export-pdf")
@role_required("ADMIN")
def export_reports_pdf():
    total_students = Student.query.count()
    total_classes = Class.query.count()
    
    current_month = dt.date.today().strftime('%Y-%m')
    current_month_revenue = db.session.query(func.sum(Invoice.total_amount))\
        .filter(Invoice.status == "PAID", Invoice.billing_month == current_month)\
        .scalar() or 0
    
    class_sizes = (
        db.session.query(Class.id, Class.name, func.count(Student.id).label("student_count"))
        .outerjoin(Student, Student.class_id == Class.id)
        .group_by(Class.id, Class.name)
        .order_by(Class.name)
        .all()
    )

    gender_counts = (
        db.session.query(Student.gender, func.count(Student.id))
        .group_by(Student.gender)
        .all()
    )
    gender = {"M": 0, "F": 0}
    for g, c in gender_counts:
        gender[g] = int(c)

    revenue_rows = (
        db.session.query(Invoice.billing_month, func.sum(Invoice.total_amount))
        .filter(Invoice.status == "PAID")
        .group_by(Invoice.billing_month)
        .order_by(Invoice.billing_month.desc())
        .limit(6)
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
    
    elements.append(Paragraph("BÁO CÁO THỐNG KÊ HỆ THỐNG", title_style))
    elements.append(Paragraph(f"Ngày xuất: {dt.date.today().strftime('%d/%m/%Y')}", normal_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("TỔNG QUAN HỆ THỐNG", heading_style))
    overview_data = [
        ['Chỉ tiêu', 'Giá trị'],
        ['Tổng số học sinh', str(total_students)],
        ['Tổng số lớp học', str(total_classes)],
        ['Doanh thu tháng này', f"{current_month_revenue:,} VND"],
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
    
    elements.append(Paragraph("TỶ LỆ GIỚI TÍNH", heading_style))
    gender_data = [
        ['Giới tính', 'Số lượng', 'Tỷ lệ %'],
        ['Nam', str(gender['M']), f"{(gender['M']/total_students*100) if total_students > 0 else 0:.1f}%"],
        ['Nữ', str(gender['F']), f"{(gender['F']/total_students*100) if total_students > 0 else 0:.1f}%"],
    ]
    gender_table = Table(gender_data, colWidths=[5*cm, 5*cm, 6*cm])
    gender_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(gender_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("SĨ SỐ TỪNG LỚP", heading_style))
    class_data = [['Lớp', 'Sĩ số']]
    for cls_id, cls_name, count in class_sizes:
        class_data.append([cls_name, str(count)])
    class_table = Table(class_data, colWidths=[10*cm, 6*cm])
    class_table.setStyle(TableStyle([
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
    elements.append(class_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("DOANH THU CÁC THÁNG", heading_style))
    revenue_data = [['Tháng', 'Doanh thu (VND)']]
    for month, total in revenue_rows:
        revenue_data.append([month, f"{int(total or 0):,}"])
    revenue_table = Table(revenue_data, colWidths=[8*cm, 8*cm])
    revenue_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(revenue_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'bao_cao_admin_{dt.date.today().strftime("%Y%m%d")}.pdf'
    )
