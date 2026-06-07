from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from population_insight.db.connection import (
    execute_write,
    fetch_all,
    fetch_one,
    get_connection,
    get_integrity_error_types,
    is_unique_constraint_error,
)
from population_insight.services.log_service import log_operation
from population_insight.services.population_service import query_population_records
from population_insight.utils.validators import (
    ensure_non_negative_number,
    ensure_text,
    ensure_year,
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def list_regions() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM regions ORDER BY name ASC")


def add_region(data: dict[str, Any], username: str = "system") -> int:
    name = ensure_text(data.get("name"), "地区名称")
    region_type = ensure_text(data.get("region_type"), "地区类型")
    values = (
        name,
        region_type,
        _clean(data.get("admin_code")),
        _clean(data.get("parent_region")),
        _clean(data.get("remarks")),
    )
    try:
        record_id = execute_write(
            """
            INSERT INTO regions (name, region_type, admin_code, parent_region, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            values,
        )
    except get_integrity_error_types() as error:
        raise ValueError("地区名称已存在。") from error
    log_operation(username, "ADD_REGION", record_id, name)
    return record_id


def list_data_sources() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM data_sources ORDER BY created_at DESC, id DESC")


def add_data_source(data: dict[str, Any], username: str = "system") -> int:
    name = ensure_text(data.get("name"), "来源名称")
    publisher = ensure_text(data.get("publisher"), "发布机构")
    reliability_level = _clean(data.get("reliability_level")) or "中"
    if reliability_level not in {"高", "中", "低"}:
        raise ValueError("可信等级只能是高、中、低。")
    published_date = _clean(data.get("published_date"))
    if published_date:
        try:
            datetime.strptime(published_date, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("发布日期必须使用 YYYY-MM-DD 格式。") from error
    values = (
        name,
        publisher,
        _clean(data.get("source_url")),
        published_date,
        reliability_level,
        _clean(data.get("remarks")),
    )
    try:
        record_id = execute_write(
            """
            INSERT INTO data_sources (
                name, publisher, source_url, published_date, reliability_level, remarks
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    except get_integrity_error_types() as error:
        raise ValueError("数据来源名称已存在。") from error
    log_operation(username, "ADD_DATA_SOURCE", record_id, name)
    return record_id


def list_population_indicators() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM population_indicators ORDER BY code ASC")


def add_population_indicator(data: dict[str, Any], username: str = "system") -> int:
    code = ensure_text(data.get("code"), "指标编码")
    name = ensure_text(data.get("name"), "指标名称")
    unit = ensure_text(data.get("unit"), "单位")
    try:
        record_id = execute_write(
            """
            INSERT INTO population_indicators (code, name, unit, description)
            VALUES (?, ?, ?, ?)
            """,
            (code, name, unit, _clean(data.get("description"))),
        )
    except get_integrity_error_types() as error:
        raise ValueError("指标编码已存在。") from error
    log_operation(username, "ADD_INDICATOR", record_id, code)
    return record_id


def list_annual_indicator_values() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            v.id,
            v.region,
            v.year,
            v.indicator_code,
            i.name AS indicator_name,
            i.unit,
            v.value,
            v.remarks,
            v.created_at
        FROM annual_indicator_values v
        LEFT JOIN population_indicators i ON i.code = v.indicator_code
        ORDER BY v.year DESC, v.region ASC, v.indicator_code ASC
        """
    )


def add_annual_indicator_value(data: dict[str, Any], username: str = "system") -> int:
    region = ensure_text(data.get("region"), "地区")
    year = ensure_year(data.get("year"))
    indicator_code = ensure_text(data.get("indicator_code"), "指标编码")
    value = ensure_non_negative_number(data.get("value"), "指标值")
    if not fetch_one("SELECT 1 FROM population_indicators WHERE code = ?", (indicator_code,)):
        raise ValueError("指标编码不存在。")
    try:
        record_id = execute_write(
            """
            INSERT INTO annual_indicator_values (
                region, year, indicator_code, value, remarks
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (region, year, indicator_code, value, _clean(data.get("remarks"))),
        )
    except get_integrity_error_types() as error:
        if is_unique_constraint_error(error):
            raise ValueError("同一地区、年份、指标的扩展值已存在。") from error
        raise ValueError("年度扩展指标值保存失败。") from error
    log_operation(username, "ADD_INDICATOR_VALUE", record_id, f"{region}-{year}-{indicator_code}")
    return record_id


def list_analysis_reports() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM analysis_reports ORDER BY created_at DESC, id DESC")


def add_analysis_report(data: dict[str, Any], username: str = "system") -> int:
    title = ensure_text(data.get("title"), "报告标题")
    report_summary = ensure_text(data.get("report_summary"), "分析摘要")
    filter_summary = _clean(data.get("filter_summary"))
    record_id = execute_write(
        """
        INSERT INTO analysis_reports (title, username, filter_summary, report_summary)
        VALUES (?, ?, ?, ?)
        """,
        (title, username, filter_summary, report_summary),
    )
    log_operation(username, "ADD_ANALYSIS_REPORT", record_id, title)
    return record_id


def build_statistics_report_summary(statistics: dict[str, Any], filters: dict[str, Any]) -> str:
    filter_summary = json.dumps(filters, ensure_ascii=False)
    return (
        f"筛选条件：{filter_summary}；"
        f"记录数：{statistics['record_count']}；"
        f"平均总人口：{statistics['avg_total_population']:.0f}；"
        f"平均出生率：{statistics['avg_birth_rate']:.2f}；"
        f"平均老龄化率：{statistics['avg_aging_rate']:.2f}。"
    )


def get_population_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for record in query_population_records():
        if record["aging_rate"] >= 20:
            alerts.append(_alert(record, "老龄化率较高", "高", f"老龄化率 {record['aging_rate']:.2f}%"))
        if record["natural_growth_rate"] < 0:
            alerts.append(
                _alert(record, "自然增长率为负", "高", f"自然增长率 {record['natural_growth_rate']:.2f}%")
            )
        if record["birth_rate"] < 7:
            alerts.append(_alert(record, "出生率偏低", "中", f"出生率 {record['birth_rate']:.2f}%"))
    severity_rank = {"高": 2, "中": 1, "低": 0}
    return sorted(
        alerts,
        key=lambda item: (item["year"], severity_rank.get(item["severity"], 0), item["region"]),
        reverse=True,
    )


def get_extension_counts() -> dict[str, int]:
    with get_connection() as connection:
        table_names = [
            "regions",
            "data_sources",
            "population_indicators",
            "annual_indicator_values",
            "analysis_reports",
        ]
        return {
            table: _first_value(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone())
            for table in table_names
        }


def _first_value(row: dict[str, Any] | tuple | None) -> Any:
    if row is None:
        return 0
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def _alert(record: dict[str, Any], alert_type: str, severity: str, message: str) -> dict[str, Any]:
    return {
        "region": record["region"],
        "year": record["year"],
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
    }
