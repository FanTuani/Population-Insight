from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from population_insight.config import CHART_DIR, METRIC_LABELS
from population_insight.services.population_service import query_population_records

plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang SC",
    "Hiragino Sans GB",
    "SimHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def _build_chart_path(prefix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return CHART_DIR / f"{prefix}_{timestamp}.png"


def draw_trend_chart(region: str, metric: str) -> str:
    records = [
        item
        for item in query_population_records({"region": region})
        if item["region"] == region
    ]
    if not records:
        raise ValueError("该地区没有可视化数据。")
    if metric not in METRIC_LABELS:
        raise ValueError("不支持的图表指标。")

    records.sort(key=lambda item: item["year"])
    years = [item["year"] for item in records]
    values = [item[metric] for item in records]

    plt.figure(figsize=(9, 5))
    plt.plot(years, values, marker="o", linewidth=2, color="#2f6fed")
    plt.title(f"{region}{METRIC_LABELS[metric]}趋势图")
    plt.xlabel("年份")
    plt.ylabel(METRIC_LABELS[metric])
    plt.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()

    chart_path = _build_chart_path(f"trend_{region}_{metric}")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return str(chart_path)


def draw_bar_chart(year: int, metric: str) -> str:
    records = query_population_records({"year": year})
    if not records:
        raise ValueError("该年份没有可视化数据。")
    if metric not in METRIC_LABELS:
        raise ValueError("不支持的图表指标。")

    regions = [item["region"] for item in records]
    values = [item[metric] for item in records]

    plt.figure(figsize=(10, 5))
    plt.bar(regions, values, color="#18a16d")
    plt.title(f"{year}年各地区{METRIC_LABELS[metric]}对比图")
    plt.xlabel("地区")
    plt.ylabel(METRIC_LABELS[metric])
    plt.xticks(rotation=20)
    plt.tight_layout()

    chart_path = _build_chart_path(f"bar_{year}_{metric}")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return str(chart_path)


def draw_gender_pie_chart(region: str, year: int) -> str:
    records = [
        item
        for item in query_population_records({"region": region, "year": year})
        if item["region"] == region
    ]
    if not records:
        raise ValueError("该地区该年份没有可视化数据。")

    record = records[0]
    plt.figure(figsize=(6, 6))
    plt.pie(
        [record["male_population"], record["female_population"]],
        labels=["男性人口", "女性人口"],
        autopct="%1.1f%%",
        colors=["#5b8ff9", "#f08bb4"],
        startangle=90,
    )
    plt.title(f"{region}{year}年人口性别结构图")
    plt.tight_layout()

    chart_path = _build_chart_path(f"pie_{region}_{year}")
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return str(chart_path)
