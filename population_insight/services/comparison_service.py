from __future__ import annotations

from typing import Any

from population_insight.config import METRIC_LABELS
from population_insight.services.national_series_service import list_national_metric_records
from population_insight.services.population_service import get_distinct_regions, query_population_records


def build_region_comparison(
    regions: list[str] | None = None,
    metric: str = "total_population",
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    if metric not in METRIC_LABELS:
        raise ValueError("不支持的对比指标。")

    selected_regions = [region.strip() for region in (regions or []) if region.strip()]
    if not selected_regions:
        selected_regions = get_distinct_regions()[:5]
    if not selected_regions:
        raise ValueError("当前没有可对比的地区数据。")

    records = query_population_records({"start_year": start_year, "end_year": end_year})
    records = [record for record in records if record["region"] in selected_regions]
    if "全国" in selected_regions:
        records.extend(
            list_national_metric_records(
                metric=metric,
                start_year=start_year,
                end_year=end_year,
            )
        )
    if not records:
        raise ValueError("当前条件下没有可对比的数据。")

    years = sorted({record["year"] for record in records})
    grouped: dict[str, dict[int, dict[str, Any]]] = {
        region: {} for region in selected_regions
    }
    for record in records:
        grouped.setdefault(record["region"], {})[record["year"]] = record

    series = []
    for region in selected_regions:
        region_points = grouped.get(region, {})
        series.append(
            {
                "name": region,
                "data": [
                    region_points[year][metric] if year in region_points else None
                    for year in years
                ],
            }
        )

    table_rows = []
    for year in years:
        values = {
            region: grouped.get(region, {}).get(year, {}).get(metric)
            for region in selected_regions
        }
        table_rows.append({"year": year, "values": values})

    summaries = _build_region_summaries(grouped, selected_regions, metric)
    latest_rank = sorted(
        [summary for summary in summaries if summary["latest_value"] is not None],
        key=lambda item: item["latest_value"],
        reverse=True,
    )
    for index, item in enumerate(latest_rank, start=1):
        item["rank"] = index

    return {
        "title": f"{METRIC_LABELS[metric]}地区对比分析",
        "metric": metric,
        "metric_label": METRIC_LABELS[metric],
        "axis_unit": _infer_axis_unit(metric),
        "regions": selected_regions,
        "years": years,
        "series": series,
        "table_rows": table_rows,
        "summaries": summaries,
        "latest_rank": latest_rank,
    }


def _build_region_summaries(
    grouped: dict[str, dict[int, dict[str, Any]]],
    regions: list[str],
    metric: str,
) -> list[dict[str, Any]]:
    summaries = []
    for region in regions:
        records = list(grouped.get(region, {}).values())
        records.sort(key=lambda item: item["year"])
        if not records:
            summaries.append(
                {
                    "region": region,
                    "start_year": None,
                    "end_year": None,
                    "start_value": None,
                    "latest_value": None,
                    "change_value": None,
                    "change_percent": None,
                    "average_value": None,
                    "rank": None,
                }
            )
            continue
        start_record = records[0]
        latest_record = records[-1]
        start_value = start_record[metric]
        latest_value = latest_record[metric]
        change_value = latest_value - start_value
        change_percent = (change_value / start_value * 100) if start_value else 0.0
        summaries.append(
            {
                "region": region,
                "start_year": start_record["year"],
                "end_year": latest_record["year"],
                "start_value": start_value,
                "latest_value": latest_value,
                "change_value": change_value,
                "change_percent": round(change_percent, 2),
                "average_value": sum(record[metric] for record in records) / len(records),
                "rank": None,
            }
        )
    return summaries


def _infer_axis_unit(metric: str) -> str:
    if metric in {"total_population", "male_population", "female_population"}:
        return "person"
    if metric in {"birth_rate", "death_rate", "natural_growth_rate", "aging_rate", "urbanization_rate"}:
        return "%"
    return ""
