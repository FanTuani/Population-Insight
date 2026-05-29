from __future__ import annotations

from population_insight.config import METRIC_LABELS
from population_insight.db.connection import fetch_one
from population_insight.services.log_service import list_operation_logs
from population_insight.services.population_service import (
    get_distinct_regions,
    get_distinct_years,
    query_population_records,
)


def get_dashboard_summary() -> dict:
    summary = fetch_one(
        """
        SELECT
            COUNT(*) AS total_records,
            MIN(year) AS min_year,
            MAX(year) AS max_year,
            AVG(total_population) AS avg_population
        FROM population_data
        """
    ) or {}

    regions = get_distinct_regions()
    years = get_distinct_years()
    latest_year = years[-1] if years else None
    latest_records = query_population_records({"year": latest_year}) if latest_year else []
    recent_logs = list_operation_logs(limit=6)

    top_region = None
    if latest_records:
        top_record = max(latest_records, key=lambda item: item["total_population"])
        top_region = {
            "region": top_record["region"],
            "year": top_record["year"],
            "total_population": top_record["total_population"],
        }

    return {
        "total_records": summary.get("total_records", 0) or 0,
        "region_count": len(regions),
        "min_year": summary.get("min_year"),
        "max_year": summary.get("max_year"),
        "avg_population": round(summary.get("avg_population", 0) or 0, 2),
        "latest_year": latest_year,
        "top_region": top_region,
        "regions": regions,
        "years": years,
        "recent_logs": recent_logs,
    }


def get_chart_trend_data(region: str, metric: str) -> dict:
    return get_chart_trend_data_with_mode(region, metric, mode="relative")


def get_chart_trend_data_with_mode(region: str, metric: str, mode: str = "relative") -> dict:
    if metric not in METRIC_LABELS:
        raise ValueError("不支持的图表指标。")
    if mode not in {"relative", "absolute"}:
        raise ValueError("不支持的趋势图展示方式。")

    records = [
        item
        for item in query_population_records({"region": region})
        if item["region"] == region
    ]
    if not records:
        raise ValueError("该地区没有可视化数据。")

    records.sort(key=lambda item: item["year"])
    raw_series = [item[metric] for item in records]
    base_value = raw_series[0]

    if mode == "relative":
        if base_value == 0:
            series = [0 for _ in raw_series]
        else:
            series = [round((value - base_value) / base_value * 100, 2) for value in raw_series]
        metric_label = "较基期变化"
        axis_unit = "%"
        title_suffix = "相对变化趋势图"
    else:
        series = raw_series
        metric_label = METRIC_LABELS[metric]
        axis_unit = _infer_axis_unit(metric)
        title_suffix = "趋势图"

    return {
        "title": f"{region}{METRIC_LABELS[metric]}{title_suffix}",
        "xAxis": [item["year"] for item in records],
        "series": series,
        "rawSeries": raw_series,
        "metricLabel": metric_label,
        "rawMetricLabel": METRIC_LABELS[metric],
        "axisUnit": axis_unit,
        "rawAxisUnit": _infer_axis_unit(metric),
        "mode": mode,
        "baseValue": base_value,
    }


def get_chart_bar_data(year: int, metric: str) -> dict:
    if metric not in METRIC_LABELS:
        raise ValueError("不支持的图表指标。")

    records = query_population_records({"year": year})
    if not records:
        raise ValueError("该年份没有可视化数据。")

    records.sort(key=lambda item: item[metric], reverse=True)
    return {
        "title": f"{year}年各地区{METRIC_LABELS[metric]}对比图",
        "xAxis": [item["region"] for item in records],
        "series": [item[metric] for item in records],
        "metricLabel": METRIC_LABELS[metric],
        "axisUnit": _infer_axis_unit(metric),
    }


def get_chart_gender_data(region: str, year: int) -> dict:
    records = [
        item
        for item in query_population_records({"region": region, "year": year})
        if item["region"] == region
    ]
    if not records:
        raise ValueError("该地区该年份没有可视化数据。")

    record = records[0]
    return {
        "title": f"{region}{year}年人口性别结构图",
        "labels": ["男性人口", "女性人口"],
        "series": [record["male_population"], record["female_population"]],
    }


def _infer_axis_unit(metric: str) -> str:
    if metric in {"total_population", "male_population", "female_population"}:
        return "person"
    if metric in {"birth_rate", "death_rate", "natural_growth_rate", "aging_rate", "urbanization_rate"}:
        return "%"
    return ""
