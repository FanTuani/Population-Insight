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
from population_insight.services.collection_service import (
    collect_population_records,
    decode_records,
    encode_records,
    import_collected_records,
)
from population_insight.services.comparison_service import build_region_comparison
from population_insight.services.dashboard_service import (
    get_chart_bar_data,
    get_chart_gender_data,
    get_chart_trend_data,
    get_chart_trend_data_with_mode,
    get_dashboard_summary,
    get_global_data_health,
)
from population_insight.services.export_service import export_to_csv
from population_insight.services.extension_service import (
    add_analysis_report,
    add_annual_indicator_value,
    add_data_source,
    add_population_indicator,
    add_region,
    build_statistics_report_summary,
    get_population_alerts,
    list_analysis_reports,
    list_annual_indicator_values,
    list_data_sources,
    list_population_indicators,
    list_regions,
)
from population_insight.services.log_service import list_operation_logs, log_operation
from population_insight.services.national_series_service import (
    build_national_population_prediction,
    get_national_series_summary,
    get_national_trend_data,
    list_national_series,
)
from population_insight.services.population_service import (
    add_population_record,
    get_analysis_regions,
    get_distinct_regions,
    get_distinct_years,
    get_population_record_by_id,
    query_population_records,
    sort_population_records,
    update_population_record,
    delete_population_record,
)
from population_insight.services.prediction_service import build_population_prediction
from population_insight.services.statistics_service import (
    calculate_statistics,
    get_region_ranking,
)
from population_insight.web.auth import admin_required, get_current_user, login_required
from population_insight.utils.validators import ensure_non_negative_number, ensure_year

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("POPULATION_INSIGHT_SECRET_KEY", FLASK_SECRET_KEY)


def _base_context() -> dict:
    years = get_distinct_years()
    national_years = list(range(1950, 2026))
    return {
        "metric_options": METRIC_LABELS,
        "region_options": get_analysis_regions(),
        "province_region_options": get_distinct_regions(),
        "year_options": sorted(set(years + national_years)),
        "province_year_options": years,
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


def _parse_page(value: str | None) -> int:
    try:
        return int(value or 1)
    except (TypeError, ValueError):
        return 1


def _parse_optional_year(value: str | None) -> int | None:
    value = _clean_text(value)
    return ensure_year(value) if value else None


@app.before_request
def load_user() -> None:
    g.user = get_current_user()


@app.context_processor
def inject_globals():
    return {
        "current_user": g.get("user"),
        "metric_options": METRIC_LABELS,
        "data_health": get_global_data_health() if g.get("user") else None,
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
    page = _parse_page(request.args.get("page"))

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
        region_options=get_distinct_regions(),
    )


@app.route("/collection", methods=["GET", "POST"])
@admin_required
def collection_view():
    form_data = request.form.to_dict()
    preview_records: list[dict] = []
    records_payload = ""
    import_summary = None

    if request.method == "POST":
        action = _clean_text(request.form.get("action")) or "preview"
        try:
            if action == "import":
                preview_records = decode_records(request.form.get("records_payload", ""))
                source_name = _clean_text(request.form.get("source_name"))
                source_url = _clean_text(request.form.get("source_url"))
                quality = _clean_text(request.form.get("data_quality")) or "official_verified"
                aging_basis = _clean_text(request.form.get("aging_rate_basis")) or "60_plus"
                preview_records = [
                    {
                        **record,
                        "data_source_name": record.get("data_source_name") or source_name,
                        "source_url": record.get("source_url") or source_url,
                        "data_quality": record.get("data_quality") or quality,
                        "aging_rate_basis": record.get("aging_rate_basis") or aging_basis,
                    }
                    for record in preview_records
                ]
                import_summary = import_collected_records(preview_records, username=g.user["username"])
                log_operation(
                    g.user["username"],
                    "IMPORT_COLLECTED_RECORDS",
                    details=f"imported={import_summary['imported']}, failed={import_summary['failed']}",
                )

                publisher = _clean_text(request.form.get("publisher"))
                if source_name and publisher:
                    try:
                        add_data_source(
                            {
                                "name": source_name,
                                "publisher": publisher,
                                "source_url": _clean_text(request.form.get("source_url")),
                                "published_date": _clean_text(request.form.get("published_date")),
                                "reliability_level": _clean_text(request.form.get("reliability_level")) or "高",
                                "remarks": _clean_text(request.form.get("source_remarks")) or "人口数据采集导入",
                            },
                            username=g.user["username"],
                        )
                    except ValueError as source_error:
                        flash(f"数据来源整理提示：{source_error}", "warning")

                level = "success" if import_summary["failed"] == 0 else "warning"
                flash(
                    f"采集导入完成：成功 {import_summary['imported']} 条，失败 {import_summary['failed']} 条。",
                    level,
                )
                records_payload = encode_records(preview_records)
                if import_summary["failed"] == 0:
                    return redirect(url_for("records_view"))
            else:
                result = collect_population_records(
                    raw_text=request.form.get("raw_text", ""),
                    source_url=_clean_text(request.form.get("source_url")),
                )
                preview_records = result["records"]
                records_payload = encode_records(preview_records)
                flash(f"已识别 {len(preview_records)} 条人口记录，请核对后导入。", "success")
        except ValueError as error:
            flash(str(error), "error")

    return render_template(
        "collection.html",
        form_data=form_data,
        preview_records=preview_records,
        records_payload=records_payload,
        import_summary=import_summary,
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

    return render_template(
        "record_form.html",
        mode="create",
        form_data=form_data,
        region_options=get_distinct_regions(),
    )


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
        region_options=get_distinct_regions(),
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


@app.route("/statistics", methods=["GET", "POST"])
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
        try:
            ranking = get_region_ranking(metric="total_population", year=ranking_year, top_n=5)
        except ValueError:
            ranking = []
        if request.method == "POST" and statistics:
            report_title = _clean_text(request.form.get("title")) or "统计分析报告"
            filters = {
                "region": region or "全部地区",
                "start_year": start_year_text or "不限",
                "end_year": end_year_text or "不限",
            }
            add_analysis_report(
                {
                    "title": report_title,
                    "filter_summary": str(filters),
                    "report_summary": build_statistics_report_summary(statistics, filters),
                },
                username=g.user["username"],
            )
            flash("分析报告已保存。", "success")
            return redirect(url_for("reports_view"))
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
    default_region = "全国"
    default_year = context["province_year_options"][-1] if context["province_year_options"] else ""
    return render_template(
        "charts.html",
        default_region=default_region,
        default_year=default_year,
        **context,
    )


@app.route("/national-series")
@login_required
def national_series_view():
    records = list_national_series()
    summary = get_national_series_summary()
    forecast_years_text = _clean_text(request.args.get("forecast_years")) or "5"
    prediction = None
    error_message = None
    try:
        prediction = build_national_population_prediction(int(forecast_years_text))
    except (TypeError, ValueError) as error:
        error_message = str(error)

    return render_template(
        "national_series.html",
        records=records,
        summary=summary,
        prediction=prediction,
        forecast_years=forecast_years_text,
        error_message=error_message,
    )


@app.route("/prediction", methods=["GET", "POST"])
@login_required
def prediction_view():
    context = _base_context()
    default_region = context["region_options"][0] if context["region_options"] else ""
    region = _clean_text(request.values.get("region")) or default_region
    metric = _clean_text(request.values.get("metric")) or "total_population"
    forecast_years_text = _clean_text(request.values.get("forecast_years")) or "5"
    prediction = None
    error_message = None

    try:
        forecast_years = int(forecast_years_text)
        if region == "全国":
            if metric != "total_population":
                raise ValueError("全国长序列预测目前仅支持总人口。")
            national_prediction = build_national_population_prediction(forecast_years)
            prediction = {
                "region": "全国",
                "metric": "total_population",
                "metric_label": "总人口",
                "history": national_prediction["history"],
                "predictions": [
                    {
                        "year": item["year"],
                        "linear_value": item["predicted_value"],
                        "growth_fit_value": item["predicted_value"],
                        "recent_trend_value": item["predicted_value"],
                        "predicted_value": item["predicted_value"],
                    }
                    for item in national_prediction["predictions"]
                ],
                "model": {
                    **national_prediction["model"],
                    "compound_growth_rate": 0,
                    "recent_growth_rate": 0,
                },
                "structure": {
                    "male_ratio_start": 0,
                    "male_ratio_latest": 0,
                    "aging_delta": 0,
                    "birth_delta": 0,
                    "urbanization_delta": 0,
                    "findings": ["全国预测基于 1950-2025 年总人口长序列。"],
                },
                "risk": {
                    "score": 0,
                    "level": "观察",
                    "factors": ["全国长序列预测用于宏观趋势观察。"],
                    "suggestion": "建议结合出生率、死亡率和自然增长率进行解释。",
                },
                "explanation": {
                    "provider": "local-rule",
                    "text": "全国预测使用 1950-2025 年总人口长序列进行线性拟合，适合答辩展示长期人口规模变化方向。",
                },
                "chart": {
                    "title": "全国总人口历史趋势与预测",
                    "xAxis": [item["year"] for item in national_prediction["history"]]
                    + [item["year"] for item in national_prediction["predictions"]],
                    "history": [item["value"] for item in national_prediction["history"]]
                    + [None for _ in national_prediction["predictions"]],
                    "prediction": [None for _ in national_prediction["history"][:-1]]
                    + [national_prediction["history"][-1]["value"]]
                    + [item["predicted_value"] for item in national_prediction["predictions"]],
                    "metricLabel": "总人口",
                    "axisUnit": "person",
                    "splitYear": national_prediction["history"][-1]["year"],
                },
            }
        else:
            prediction = build_population_prediction(region, metric, forecast_years)
        if request.method == "POST" and _clean_text(request.form.get("action")) == "save_report":
            add_analysis_report(
                {
                    "title": _clean_text(request.form.get("title")) or f"{region}人口趋势预测报告",
                    "filter_summary": f"region={region}, metric={metric}, forecast_years={forecast_years}",
                    "report_summary": prediction["explanation"]["text"],
                },
                username=g.user["username"],
            )
            flash("预测分析报告已保存。", "success")
            return redirect(url_for("reports_view"))
    except (TypeError, ValueError) as error:
        error_message = str(error)

    return render_template(
        "prediction.html",
        prediction=prediction,
        filters={
            "region": region,
            "metric": metric,
            "forecast_years": forecast_years_text,
        },
        error_message=error_message,
        **context,
    )


@app.route("/comparison")
@login_required
def comparison_view():
    context = _base_context()
    selected_regions = request.args.getlist("regions")
    if not selected_regions:
        selected_regions = ["全国"] + context["province_region_options"][:1]
    metric = _clean_text(request.args.get("metric")) or "total_population"
    start_year_text = _clean_text(request.args.get("start_year"))
    end_year_text = _clean_text(request.args.get("end_year"))

    comparison = None
    error_message = None
    try:
        comparison = build_region_comparison(
            regions=selected_regions,
            metric=metric,
            start_year=_parse_optional_year(start_year_text),
            end_year=_parse_optional_year(end_year_text),
        )
    except ValueError as error:
        error_message = str(error)

    return render_template(
        "comparison.html",
        comparison=comparison,
        filters={
            "regions": selected_regions,
            "metric": metric,
            "start_year": start_year_text,
            "end_year": end_year_text,
        },
        error_message=error_message,
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


@app.route("/settings")
@admin_required
def settings_view():
    return render_template("settings.html")


@app.route("/users")
@admin_required
def users_view():
    from population_insight.db.connection import fetch_all

    users = fetch_all("SELECT id, username, role, created_at FROM users ORDER BY username ASC")
    return render_template("users.html", users=users)


@app.route("/permissions")
@admin_required
def permissions_view():
    permissions = [
        {"role": "admin", "scope": "全部页面、数据写入、系统维护、日志审计"},
        {"role": "viewer", "scope": "概览、数据浏览、统计、对比、预测、图表、预警、报告浏览"},
    ]
    return render_template("permissions.html", permissions=permissions)


@app.route("/regions", methods=["GET", "POST"])
@admin_required
def regions_view():
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            add_region(form_data, username=g.user["username"])
            flash("地区档案已新增。", "success")
            return redirect(url_for("regions_view"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template("regions.html", regions=list_regions(), form_data=form_data)


@app.route("/sources", methods=["GET", "POST"])
@admin_required
def sources_view():
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            add_data_source(form_data, username=g.user["username"])
            flash("数据来源已新增。", "success")
            return redirect(url_for("sources_view"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template("sources.html", sources=list_data_sources(), form_data=form_data)


@app.route("/indicators", methods=["GET", "POST"])
@admin_required
def indicators_view():
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            add_population_indicator(form_data, username=g.user["username"])
            flash("扩展指标已新增。", "success")
            return redirect(url_for("indicators_view"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template(
        "indicators.html",
        indicators=list_population_indicators(),
        values=list_annual_indicator_values(),
        regions=get_distinct_regions(),
        form_data=form_data,
    )


@app.route("/indicator-values", methods=["POST"])
@admin_required
def indicator_values_create_view():
    try:
        add_annual_indicator_value(request.form.to_dict(), username=g.user["username"])
        flash("年度扩展指标值已新增。", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("indicators_view"))


@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports_view():
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            add_analysis_report(form_data, username=g.user["username"])
            flash("分析报告已新增。", "success")
            return redirect(url_for("reports_view"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template("reports.html", reports=list_analysis_reports(), form_data=form_data)


@app.route("/alerts")
@login_required
def alerts_view():
    alerts = get_population_alerts()
    return render_template("alerts.html", alerts=alerts)


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
        sort_by = _clean_text(request.args.get("sort_by")) or "value"
        sort_order = _clean_text(request.args.get("sort_order")) or "desc"
        return jsonify({"success": True, "data": get_chart_bar_data(year, metric, sort_by, sort_order)})
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


@app.route("/api/prediction/chart")
@login_required
def prediction_chart_api():
    try:
        region = _clean_text(request.args.get("region"))
        metric = _clean_text(request.args.get("metric")) or "total_population"
        forecast_years = int(_clean_text(request.args.get("forecast_years")) or "5")
        if region == "全国":
            if metric != "total_population":
                raise ValueError("全国长序列预测目前仅支持总人口。")
            national_prediction = build_national_population_prediction(forecast_years)
            history_years = [item["year"] for item in national_prediction["history"]]
            future_years = [item["year"] for item in national_prediction["predictions"]]
            history_values = [item["value"] for item in national_prediction["history"]]
            predicted_values = [item["predicted_value"] for item in national_prediction["predictions"]]
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "title": "全国总人口历史趋势与预测",
                        "xAxis": history_years + future_years,
                        "history": history_values + [None for _ in future_years],
                        "prediction": [None for _ in history_years[:-1]] + [history_values[-1]] + predicted_values,
                        "metricLabel": "总人口",
                        "axisUnit": "person",
                        "splitYear": history_years[-1],
                    },
                }
            )
        prediction = build_population_prediction(region, metric, forecast_years)
        return jsonify({"success": True, "data": prediction["chart"]})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@app.route("/api/comparison")
@login_required
def comparison_api():
    try:
        data = build_region_comparison(
            regions=request.args.getlist("regions"),
            metric=_clean_text(request.args.get("metric")) or "total_population",
            start_year=_parse_optional_year(request.args.get("start_year")),
            end_year=_parse_optional_year(request.args.get("end_year")),
        )
        return jsonify({"success": True, "data": data})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@app.route("/api/dashboard/map")
@login_required
def dashboard_map_api():
    try:
        metric = _clean_text(request.args.get("metric")) or "total_population"
        year = ensure_year(request.args.get("year", ""))
        records = query_population_records({"year": year})
        if metric not in METRIC_LABELS:
            raise ValueError("不支持的地图指标。")
        data = [
            {
                "name": item["region"],
                "value": item[metric],
                "year": item["year"],
                "population": item["total_population"],
                "birthRate": item["birth_rate"],
                "agingRate": item["aging_rate"],
            }
            for item in records
        ]
        return jsonify(
            {
                "success": True,
                "data": {
                    "year": year,
                    "metric": metric,
                    "metricLabel": METRIC_LABELS[metric],
                    "items": data,
                },
            }
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@app.route("/api/national-series/trend")
@login_required
def national_series_trend_api():
    try:
        metric = _clean_text(request.args.get("metric")) or "total_population"
        return jsonify({"success": True, "data": get_national_trend_data(metric)})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


def create_app() -> Flask:
    init_database()
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
