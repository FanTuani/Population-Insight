from __future__ import annotations

import os
from math import ceil
from urllib.parse import urlencode

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from population_insight.config import FLASK_SECRET_KEY, METRIC_LABELS, WEB_PAGE_SIZE
from population_insight.db.initializer import init_database
from population_insight.services.auth_service import login
from population_insight.services.dashboard_service import (
    get_chart_bar_data,
    get_chart_gender_data,
    get_chart_trend_data,
    get_chart_trend_data_with_mode,
    get_dashboard_summary,
)
from population_insight.services.export_service import export_to_csv
from population_insight.services.log_service import list_operation_logs
from population_insight.services.population_service import (
    add_population_record,
    get_distinct_regions,
    get_distinct_years,
    get_population_record_by_id,
    query_population_records,
    sort_population_records,
    update_population_record,
    delete_population_record,
)
from population_insight.services.statistics_service import (
    calculate_statistics,
    get_region_ranking,
)
from population_insight.web.auth import admin_required, get_current_user, login_required
from population_insight.utils.validators import ensure_non_negative_number, ensure_year

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("POPULATION_INSIGHT_SECRET_KEY", FLASK_SECRET_KEY)


def _base_context() -> dict:
    return {
        "metric_options": METRIC_LABELS,
        "region_options": get_distinct_regions(),
        "year_options": get_distinct_years(),
    }


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _parse_record_filters(source) -> tuple[dict, dict]:
    raw_filters = {
        "region": _clean_text(source.get("region")),
        "year": _clean_text(source.get("year")),
        "start_year": _clean_text(source.get("start_year")),
        "end_year": _clean_text(source.get("end_year")),
        "min_total_population": _clean_text(source.get("min_total_population")),
        "max_total_population": _clean_text(source.get("max_total_population")),
        "min_birth_rate": _clean_text(source.get("min_birth_rate")),
        "max_birth_rate": _clean_text(source.get("max_birth_rate")),
        "min_aging_rate": _clean_text(source.get("min_aging_rate")),
        "max_aging_rate": _clean_text(source.get("max_aging_rate")),
    }

    filters: dict = {}
    if raw_filters["region"]:
        filters["region"] = raw_filters["region"]
    if raw_filters["year"]:
        filters["year"] = ensure_year(raw_filters["year"])
    if raw_filters["start_year"]:
        filters["start_year"] = ensure_year(raw_filters["start_year"])
    if raw_filters["end_year"]:
        filters["end_year"] = ensure_year(raw_filters["end_year"])

    number_fields = {
        "min_total_population": ("总人口最小值", True),
        "max_total_population": ("总人口最大值", True),
        "min_birth_rate": ("出生率最小值", False),
        "max_birth_rate": ("出生率最大值", False),
        "min_aging_rate": ("老龄化率最小值", False),
        "max_aging_rate": ("老龄化率最大值", False),
    }
    for key, (label, integer) in number_fields.items():
        if raw_filters[key]:
            filters[key] = ensure_non_negative_number(raw_filters[key], label, integer=integer)

    return filters, raw_filters


def _apply_record_sort(records: list[dict], sort_field: str, sort_order: str) -> list[dict]:
    if sort_field:
        return sort_population_records(records, sort_field, sort_order)
    return sorted(records, key=lambda item: (item["region"], -item["year"], item["id"]))


def _paginate(records: list[dict], page: int, page_size: int = WEB_PAGE_SIZE) -> dict:
    total_records = len(records)
    total_pages = max(1, ceil(total_records / page_size)) if total_records else 1
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": records[start:end],
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": total_pages,
    }


def _querystring(params: dict) -> str:
    clean_params = {key: value for key, value in params.items() if value not in ("", None)}
    return urlencode(clean_params)


@app.before_request
def load_user() -> None:
    g.user = get_current_user()


@app.context_processor
def inject_globals():
    return {
        "current_user": g.get("user"),
        "metric_options": METRIC_LABELS,
    }


@app.route("/login", methods=["GET", "POST"])
def login_view():
    if g.user:
        return redirect(url_for("dashboard_view"))

    if request.method == "POST":
        username = _clean_text(request.form.get("username"))
        password = request.form.get("password", "")
        user = login(username, password)
        if user is None:
            flash("用户名或密码错误。", "error")
            return render_template("login.html")

        session["user"] = user
        flash(f"欢迎回来，{user['username']}。", "success")
        return redirect(url_for("dashboard_view"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout_view():
    session.clear()
    flash("你已安全退出系统。", "success")
    return redirect(url_for("login_view"))


@app.route("/")
@login_required
def dashboard_view():
    summary = get_dashboard_summary()
    return render_template("dashboard.html", summary=summary)


@app.route("/records")
@login_required
def records_view():
    try:
        filters, raw_filters = _parse_record_filters(request.args)
    except ValueError as error:
        flash(str(error), "error")
        filters, raw_filters = {}, {key: _clean_text(request.args.get(key)) for key in [
            "region",
            "year",
            "start_year",
            "end_year",
            "min_total_population",
            "max_total_population",
            "min_birth_rate",
            "max_birth_rate",
            "min_aging_rate",
            "max_aging_rate",
        ]}

    sort_field = _clean_text(request.args.get("sort_field"))
    sort_order = _clean_text(request.args.get("sort_order")) or "asc"
    page = int(request.args.get("page", 1) or 1)

    records = query_population_records(filters)
    try:
        sorted_records = _apply_record_sort(records, sort_field, sort_order)
    except ValueError as error:
        flash(str(error), "error")
        sort_field = ""
        sort_order = "asc"
        sorted_records = _apply_record_sort(records, sort_field, sort_order)

    pagination = _paginate(sorted_records, page)
    query_params = {**raw_filters, "sort_field": sort_field, "sort_order": sort_order}

    return render_template(
        "records.html",
        filters=raw_filters,
        records=pagination["items"],
        pagination=pagination,
        sort_field=sort_field,
        sort_order=sort_order,
        export_query=_querystring(query_params),
        page_query=_querystring(query_params),
    )


@app.route("/records/new", methods=["GET", "POST"])
@admin_required
def record_create_view():
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            record_id = add_population_record(form_data, username=g.user["username"])
            flash(f"新增成功，记录 ID：{record_id}", "success")
            return redirect(url_for("records_view"))
        except ValueError as error:
            flash(str(error), "error")

    return render_template("record_form.html", mode="create", form_data=form_data)


@app.route("/records/<int:record_id>/edit", methods=["GET", "POST"])
@admin_required
def record_edit_view(record_id: int):
    record = get_population_record_by_id(record_id)
    if not record:
        flash("记录不存在。", "error")
        return redirect(url_for("records_view"))

    form_data = dict(record)
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            update_population_record(record_id, form_data, username=g.user["username"])
            flash("记录修改成功。", "success")
            return redirect(url_for("records_view"))
        except ValueError as error:
            flash(str(error), "error")

    return render_template(
        "record_form.html",
        mode="edit",
        form_data=form_data,
        record=record,
    )


@app.route("/records/<int:record_id>/delete", methods=["POST"])
@admin_required
def record_delete_view(record_id: int):
    try:
        delete_population_record(record_id, username=g.user["username"])
        flash("记录已删除。", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("records_view"))


@app.route("/statistics")
@login_required
def statistics_view():
    region = _clean_text(request.args.get("region")) or None
    start_year_text = _clean_text(request.args.get("start_year"))
    end_year_text = _clean_text(request.args.get("end_year"))

    statistics = None
    ranking = []
    error_message = None

    try:
        start_year = ensure_year(start_year_text) if start_year_text else None
        end_year = ensure_year(end_year_text) if end_year_text else None
        statistics = calculate_statistics(region=region, start_year=start_year, end_year=end_year)
        ranking_year = end_year or start_year
        ranking = get_region_ranking(metric="total_population", year=ranking_year, top_n=5)
    except ValueError as error:
        error_message = str(error)

    return render_template(
        "statistics.html",
        statistics=statistics,
        ranking=ranking,
        filters={
            "region": region or "",
            "start_year": start_year_text,
            "end_year": end_year_text,
        },
        error_message=error_message,
    )


@app.route("/charts")
@login_required
def charts_view():
    context = _base_context()
    default_region = context["region_options"][0] if context["region_options"] else ""
    default_year = context["year_options"][-1] if context["year_options"] else ""
    return render_template(
        "charts.html",
        default_region=default_region,
        default_year=default_year,
        **context,
    )


@app.route("/export")
@login_required
def export_records():
    try:
        filters, _ = _parse_record_filters(request.args)
        sort_field = _clean_text(request.args.get("sort_field"))
        sort_order = _clean_text(request.args.get("sort_order")) or "asc"
        records = _apply_record_sort(query_population_records(filters), sort_field, sort_order)
        path = export_to_csv(records)
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("records_view"))


@app.route("/logs")
@admin_required
def logs_view():
    logs = list_operation_logs(limit=100)
    return render_template("logs.html", logs=logs)


@app.route("/api/charts/trend")
@login_required
def chart_trend_api():
    try:
        region = _clean_text(request.args.get("region"))
        metric = _clean_text(request.args.get("metric"))
        mode = _clean_text(request.args.get("mode")) or "relative"
        return jsonify({"success": True, "data": get_chart_trend_data_with_mode(region, metric, mode)})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@app.route("/api/charts/bar")
@login_required
def chart_bar_api():
    try:
        year = ensure_year(request.args.get("year", ""))
        metric = _clean_text(request.args.get("metric"))
        return jsonify({"success": True, "data": get_chart_bar_data(year, metric)})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@app.route("/api/charts/gender")
@login_required
def chart_gender_api():
    try:
        region = _clean_text(request.args.get("region"))
        year = ensure_year(request.args.get("year", ""))
        return jsonify({"success": True, "data": get_chart_gender_data(region, year)})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


def create_app() -> Flask:
    init_database()
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
