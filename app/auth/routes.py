import datetime as dt
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from . import bp
from ..extensions import db
from ..models import User

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "ADMIN":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("teacher.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Sai tài khoản hoặc mật khẩu.", "danger")
            return render_template("auth/login.html", username=username)

        login_user(user)
        flash("Đăng nhập thành công.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("admin.dashboard" if user.role == "ADMIN" else "teacher.dashboard"))

    return render_template("auth/login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("main.home"))

@bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html")

@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        new_pw2 = request.form.get("confirm_password", "")

        if not current_user.check_password(current_pw):
            flash("Mật khẩu hiện tại không đúng.", "danger")
            return render_template("auth/change_password.html")

        if len(new_pw) < 4:
            flash("Mật khẩu mới quá ngắn (>=4 ký tự).", "danger")
            return render_template("auth/change_password.html")

        if new_pw != new_pw2:
            flash("Xác nhận mật khẩu không khớp.", "danger")
            return render_template("auth/change_password.html")

        current_user.set_password(new_pw)
        db.session.commit()
        flash("Đổi mật khẩu thành công.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/change_password.html")
