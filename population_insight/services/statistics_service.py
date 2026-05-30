from __future__ import annotations

from collections import defaultdict
from typing import Any

from population_insight.services.population_service import query_population_records


def calculate_statistics(
    region: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    records = query_population_records(
        {
            "region": region,
            "start_year": start_year,
            "end_year": end_year,
        }
    )
    if not records:
        raise ValueError("当前条件下没有数据，无法统计。")

    total_population_values = [record["total_population"] for record in records]
    birth_rate_values = [record["birth_rate"] for record in records]
    aging_rate_values = [record["aging_rate"] for record in records]

    grouped_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped_records[record["region"]].append(record)

    growth_summary = []
    for region_name, region_records in grouped_records.items():
        region_records.sort(key=lambda item: item["year"])
        start_record = region_records[0]
        end_record = region_records[-1]
        if start_record["total_population"] == 0:
            growth_percent = 0.0
        else:
            growth_percent = (
                (end_record["total_population"] - start_record["total_population"])
                / start_record["total_population"]
                * 100
            )
        growth_summary.append(
            {
                "region": region_name,
                "start_year": start_record["year"],
                "end_year": end_record["year"],
                "growth_percent": growth_percent,
            }
        )
    growth_summary.sort(key=lambda item: item["growth_percent"], reverse=True)

    return {
        "record_count": len(records),
        "avg_total_population": sum(total_population_values) / len(total_population_values),
        "avg_birth_rate": sum(birth_rate_values) / len(birth_rate_values),
        "avg_aging_rate": sum(aging_rate_values) / len(aging_rate_values),
        "max_population": max(records, key=lambda item: item["total_population"]),
        "min_population": min(records, key=lambda item: item["total_population"]),
        "growth_summary": growth_summary,
    }


def get_region_ranking(
    metric: str = "total_population", year: int | None = None, top_n: int = 10
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {"year": year} if year is not None else {}
    records = query_population_records(filters)
    if not records:
        raise ValueError("没有可用于排名的数据。")

    if metric not in records[0]:
        raise ValueError("不支持的排名指标。")

    if year is None:
        latest_year = max(item["year"] for item in records)
        records = [item for item in records if item["year"] == latest_year]

    sorted_records = sorted(records, key=lambda item: item[metric], reverse=True)
    ranking = []
    for index, item in enumerate(sorted_records[:top_n], start=1):
        ranking.append(
            {
                "rank": index,
                "region": item["region"],
                "year": item["year"],
                "metric": metric,
                "value": item[metric],
            }
        )
    return ranking
