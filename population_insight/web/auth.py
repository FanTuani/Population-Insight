from __future__ import annotations

from functools import wraps

from flask import flash, redirect, session, url_for


def get_current_user() -> dict | None:
    user = session.get("user")
    return user if isinstance(user, dict) else None


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            flash("请先登录后再访问该页面。", "warning")
            return redirect(url_for("login_view"))
        return view_func(*args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped_view(*args, **kwargs):
        user = get_current_user()
        if not user or user.get("role") != "admin":
            flash("当前账号没有该操作权限。", "error")
            return redirect(url_for("dashboard_view"))
        return view_func(*args, **kwargs)

    return wrapped_view
