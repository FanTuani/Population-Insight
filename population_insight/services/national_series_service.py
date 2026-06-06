from __future__ import annotations

import json
from statistics import mean
from typing import Any
from urllib.request import urlopen

from population_insight.db.connection import fetch_all, fetch_one

NATIONAL_METRIC_LABELS = {
    "total_population": "总人口",
    "birth_rate": "出生率",
    "death_rate": "死亡率",
    "natural_growth_rate": "自然增长率",
    "urbanization_rate": "城镇化率",
}

NATIONAL_METRIC_UNITS = {
    "total_population": "person",
    "birth_rate": "permille",
    "death_rate": "permille",
    "natural_growth_rate": "permille",
    "urbanization_rate": "%",
}

NATIONAL_SERIES_SUPPORTED_METRICS = {
    "total_population",
    "birth_rate",
    "death_rate",
    "natural_growth_rate",
    "urbanization_rate",
}

WDI_INDICATORS = {
    "total_population": "SP.POP.TOTL",
    "birth_rate": "SP.DYN.CBRT.IN",
    "death_rate": "SP.DYN.CDRT.IN",
    "urban_population": "SP.URB.TOTL",
    "urbanization_rate": "SP.URB.TOTL.IN.ZS",
}

EARLY_NATIONAL_RECORDS = [
    {
        "year": 1950,
        "total_population": 551960000,
        "birth_rate": 37.00,
        "death_rate": 18.00,
        "natural_growth_rate": 19.00,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1951,
        "total_population": 563000000,
        "birth_rate": 37.80,
        "death_rate": 17.80,
        "natural_growth_rate": 20.00,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1952,
        "total_population": 574820000,
        "birth_rate": 37.00,
        "death_rate": 17.00,
        "natural_growth_rate": 20.00,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1953,
        "total_population": 587960000,
        "birth_rate": 37.00,
        "death_rate": 14.00,
        "natural_growth_rate": 23.00,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1954,
        "total_population": 602660000,
        "birth_rate": 37.97,
        "death_rate": 13.18,
        "natural_growth_rate": 24.79,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1955,
        "total_population": 614650000,
        "birth_rate": 32.60,
        "death_rate": 12.28,
        "natural_growth_rate": 20.32,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1956,
        "total_population": 628280000,
        "birth_rate": 31.90,
        "death_rate": 11.40,
        "natural_growth_rate": 20.50,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1957,
        "total_population": 646530000,
        "birth_rate": 34.03,
        "death_rate": 10.80,
        "natural_growth_rate": 23.23,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1958,
        "total_population": 659940000,
        "birth_rate": 29.22,
        "death_rate": 11.98,
        "natural_growth_rate": 17.24,
        "urban_population": None,
        "urbanization_rate": None,
    },
    {
        "year": 1959,
        "total_population": 672070000,
        "birth_rate": 24.78,
        "death_rate": 14.59,
        "natural_growth_rate": 10.19,
        "urban_population": None,
        "urbanization_rate": None,
    },
]

NBS_2025_RECORD = {
    "year": 2025,
    "total_population": 1404890000,
    "birth_rate": 5.63,
    "death_rate": 8.04,
    "natural_growth_rate": -2.41,
    "urban_population": None,
    "urbanization_rate": None,
    "source_name": "国家统计局《中华人民共和国2025年国民经济和社会发展统计公报》",
    "source_url": "https://www.stats.gov.cn/sj/zxfb/",
    "data_quality": "official_communique",
    "remarks": "2025 年末全国人口、出生率、死亡率、自然增长率来自国家统计局统计公报；城镇人口和城镇化率待年鉴口径发布后补齐。",
}


def _decorate_record(record: dict[str, Any], source: str, url: str, quality: str, remarks: str) -> dict[str, Any]:
    return {
        "year": record["year"],
        "total_population": int(record["total_population"]),
        "birth_rate": record.get("birth_rate"),
        "death_rate": record.get("death_rate"),
        "natural_growth_rate": record.get("natural_growth_rate"),
        "urban_population": record.get("urban_population"),
        "urbanization_rate": record.get("urbanization_rate"),
        "source_name": record.get("source_name") or source,
        "source_url": record.get("source_url") or url,
        "data_quality": record.get("data_quality") or quality,
        "remarks": record.get("remarks") or remarks,
    }


def _fetch_wdi_records(timeout: int = 20) -> list[dict[str, Any]]:
    series: dict[int, dict[str, Any]] = {}
    for metric, indicator in WDI_INDICATORS.items():
        url = (
            f"https://api.worldbank.org/v2/country/CHN/indicator/{indicator}"
            "?format=json&per_page=20000&date=1960:2024"
        )
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload[1]:
            value = item.get("value")
            if value is None:
                continue
            year = int(item["date"])
            series.setdefault(year, {})[metric] = value

    records = []
    for year in sorted(series):
        item = series[year]
        if "total_population" not in item:
            continue
        birth_rate = item.get("birth_rate")
        death_rate = item.get("death_rate")
        records.append(
            {
                "year": year,
                "total_population": int(round(item["total_population"])),
                "birth_rate": round(float(birth_rate), 2) if birth_rate is not None else None,
                "death_rate": round(float(death_rate), 2) if death_rate is not None else None,
                "natural_growth_rate": (
                    round(float(birth_rate) - float(death_rate), 2)
                    if birth_rate is not None and death_rate is not None
                    else None
                ),
                "urban_population": (
                    int(round(item["urban_population"]))
                    if item.get("urban_population") is not None
                    else None
                ),
                "urbanization_rate": (
                    round(float(item["urbanization_rate"]), 2)
                    if item.get("urbanization_rate") is not None
                    else None
                ),
            }
        )
    return records


def build_seed_records() -> list[dict[str, Any]]:
    records = [
        _decorate_record(
            item,
            "国家统计局《中国统计年鉴》早期人口长序列",
            "https://www.stats.gov.cn/sj/ndsj/",
            "official_yearbook_transcribed",
            "1950-1959 年数据按国家统计局年鉴早期全国人口长序列整理。",
        )
        for item in EARLY_NATIONAL_RECORDS
    ]
    try:
        records.extend(
            _decorate_record(
                item,
                "World Bank WDI / official national statistical series",
                "https://api.worldbank.org/v2/country/CHN/indicator",
                "official_cross_checked",
                "1960-2024 indicators from World Bank WDI, cross-referenced to official national statistical source series.",
            )
            for item in _fetch_wdi_records()
        )
    except Exception:
        pass
    records.append(
        _decorate_record(
            NBS_2025_RECORD,
            NBS_2025_RECORD["source_name"],
            NBS_2025_RECORD["source_url"],
            NBS_2025_RECORD["data_quality"],
            NBS_2025_RECORD["remarks"],
        )
    )
    return sorted(records, key=lambda item: item["year"])


def list_national_series() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT *
        FROM national_population_series
        ORDER BY year ASC
        """
    )


def list_national_metric_records(
    metric: str = "total_population",
    start_year: int | None = None,
    end_year: int | None = None,
) -> list[dict[str, Any]]:
    if metric not in NATIONAL_SERIES_SUPPORTED_METRICS:
        raise ValueError("全国长序列暂不支持该指标。")

    records = []
    for item in list_national_series():
        if start_year and item["year"] < start_year:
            continue
        if end_year and item["year"] > end_year:
            continue
        if item.get(metric) is None:
            continue
        records.append(
            {
                "region": "全国",
                "year": item["year"],
                "total_population": item["total_population"],
                "birth_rate": item["birth_rate"],
                "death_rate": item["death_rate"],
                "natural_growth_rate": item["natural_growth_rate"],
                "aging_rate": None,
                "urbanization_rate": item["urbanization_rate"],
                "data_source_name": item.get("source_name", ""),
                "source_url": item.get("source_url", ""),
                "data_quality": item.get("data_quality", ""),
                "remarks": item.get("remarks", ""),
            }
        )
    return records


def get_national_series_summary() -> dict[str, Any]:
    summary = fetch_one(
        """
        SELECT
            COUNT(*) AS total_years,
            MIN(year) AS min_year,
            MAX(year) AS max_year
        FROM national_population_series
        """
    ) or {}
    records = list_national_series()
    if not records:
        return {
            "total_years": 0,
            "min_year": None,
            "max_year": None,
            "latest": None,
            "peak": None,
            "recent_growth": None,
            "avg_birth_rate_recent": None,
        }

    latest = records[-1]
    peak = max(records, key=lambda item: item["total_population"])
    previous = records[-2] if len(records) >= 2 else None
    recent_growth = (
        latest["total_population"] - previous["total_population"]
        if previous
        else None
    )
    recent_birth_values = [
        item["birth_rate"]
        for item in records[-5:]
        if item.get("birth_rate") is not None
    ]
    return {
        "total_years": summary.get("total_years", 0),
        "min_year": summary.get("min_year"),
        "max_year": summary.get("max_year"),
        "latest": latest,
        "peak": peak,
        "recent_growth": recent_growth,
        "avg_birth_rate_recent": round(mean(recent_birth_values), 2) if recent_birth_values else None,
    }


def get_national_trend_data(metric: str) -> dict[str, Any]:
    if metric not in NATIONAL_METRIC_LABELS:
        raise ValueError("不支持的全国长序列指标。")

    records = [item for item in list_national_series() if item.get(metric) is not None]
    if not records:
        raise ValueError("当前指标暂无可视化数据。")

    return {
        "title": f"1950-2025 年全国{NATIONAL_METRIC_LABELS[metric]}趋势",
        "metric": metric,
        "metricLabel": NATIONAL_METRIC_LABELS[metric],
        "axisUnit": NATIONAL_METRIC_UNITS[metric],
        "xAxis": [item["year"] for item in records],
        "series": [item[metric] for item in records],
        "source": records[-1]["source_name"],
        "sourceUrl": records[-1]["source_url"],
    }


def build_national_population_prediction(forecast_years: int = 5) -> dict[str, Any]:
    records = [item for item in list_national_series() if item.get("total_population")]
    if len(records) < 3:
        raise ValueError("全国长序列数据不足，无法预测。")
    forecast_years = max(1, min(int(forecast_years), 10))
    recent_records = records[-8:]
    model_records = records[-5:]
    years = [item["year"] for item in model_records]
    values = [float(item["total_population"]) for item in model_records]
    linear = _linear_regression(years, values)
    latest_year = recent_records[-1]["year"]
    future_years = list(range(latest_year + 1, latest_year + forecast_years + 1))
    predictions = []
    for year in future_years:
        predicted = max(0, linear["slope"] * year + linear["intercept"])
        predictions.append({"year": year, "predicted_value": int(round(predicted))})

    return {
        "history": [{"year": item["year"], "value": item["total_population"]} for item in recent_records],
        "predictions": predictions,
        "model": {
            "name": "近5年线性趋势",
            "r2": linear["r2"],
            "slope": linear["slope"],
        },
    }


def _linear_regression(years: list[int], values: list[float]) -> dict[str, float]:
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(values) / n
    ss_xx = sum((year - mean_x) ** 2 for year in years)
    slope = (
        sum((year - mean_x) * (value - mean_y) for year, value in zip(years, values)) / ss_xx
        if ss_xx
        else 0.0
    )
    intercept = mean_y - slope * mean_x
    fitted = [slope * year + intercept for year in years]
    ss_tot = sum((value - mean_y) ** 2 for value in values)
    ss_res = sum((value - fit) ** 2 for value, fit in zip(values, fitted))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return {"slope": slope, "intercept": intercept, "r2": max(0.0, min(1.0, r2))}
