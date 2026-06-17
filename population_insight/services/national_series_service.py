from __future__ import annotations

import json
import os
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

FALLBACK_WDI_ROWS = """
1960|667070000|20.86|25.43|-4.57|131717278|19.75
1961|660330000|18.02|14.24|3.78|127405724|19.29
1962|665770000|37.01|10.02|26.99|115344340|17.32
1963|682335000|43.37|10.04|33.33|114879915|16.84
1964|698355000|39.14|11.5|27.64|127798959|18.3
1965|715185000|37.88|9.5|28.38|128616573|17.98
1966|735400000|35.05|8.83|26.22|131340439|17.86
1967|754550000|33.96|8.43|25.53|133860306|17.74
1968|774510000|35.59|8.21|27.38|136471712|17.62
1969|796025000|34.11|8.03|26.08|139300169|17.5
1970|818315000|33.43|7.6|25.83|142223062|17.38
1971|841105000|30.65|7.32|23.33|145179409|17.26
1972|862030000|29.77|7.61|22.16|147681368|17.13
1973|881940000|27.93|7.04|20.89|151700685|17.2
1974|900350000|24.82|7.34|17.48|154535692|17.16
1975|916395000|23.01|7.32|15.69|158946242|17.34
1976|930685000|19.91|7.25|12.66|162279250|17.44
1977|943455000|18.93|6.87|12.06|165586908|17.55
1978|956165000|18.25|6.25|12.0|171298938|17.92
1979|969005000|17.82|6.21|11.61|183733652|18.96
1980|981235000|18.21|6.34|11.87|190272409|19.39
1981|993885000|20.91|6.36|14.55|200332315|20.16
1982|1008630000|22.28|6.6|15.68|207429825|20.57
1983|1023310000|20.19|6.9|13.29|221276090|21.62
1984|1036825000|19.9|6.82|13.08|238617693|23.01
1985|1051040000|21.04|6.78|14.26|249169098|23.71
1986|1066790000|22.43|6.86|15.57|261629348|24.52
1987|1084035000|23.33|6.72|16.61|274470133|25.32
1988|1101630000|22.37|6.64|15.73|284382176|25.81
1989|1118650000|21.58|6.54|15.04|293200950|26.21
1990|1135185000|21.06|6.67|14.39|297369675|26.2
1991|1150780000|19.68|6.7|12.98|310022970|26.94
1992|1164970000|18.27|6.64|11.63|319899240|27.46
1993|1178440000|18.09|6.64|11.45|329846252|27.99
1994|1191835000|17.7|6.49|11.21|339789820|28.51
1995|1204855000|17.12|6.57|10.55|349894476|29.04
1996|1217550000|16.98|6.56|10.42|371107586|30.48
1997|1230075000|16.57|6.51|10.06|392516368|31.91
1998|1241935000|15.64|6.5|9.14|414187388|33.35
1999|1252735000|14.64|6.46|8.18|435697538|34.78
2000|1262645000|14.03|6.45|7.58|460007123|36.43
2001|1271850000|13.38|6.43|6.95|478975457|37.66
2002|1280400000|12.86|6.41|6.45|500505578|39.09
2003|1288400000|12.41|6.4|6.01|522191502|40.53
2004|1296075000|12.29|6.42|5.87|541241096|41.76
2005|1303720000|12.4|6.51|5.89|560469200|42.99
2006|1311020000|12.09|6.81|5.28|581345729|44.34
2007|1317885000|12.1|6.93|5.17|604767464|45.89
2008|1324655000|12.14|7.06|5.08|622448838|46.99
2009|1331260000|11.95|7.08|4.87|643553786|48.34
2010|1337705000|11.9|7.11|4.79|658606042|49.23
2011|1345035000|13.27|7.14|6.13|697132024|51.83
2012|1354190000|14.57|7.13|7.44|719079105|53.1
2013|1363240000|13.03|7.13|5.9|742829499|54.49
2014|1371860000|13.83|7.12|6.71|764815456|55.75
2015|1379860000|11.99|7.07|4.92|791070763|57.33
2016|1387790000|13.57|7.04|6.53|816574579|58.84
2017|1396215000|12.64|7.06|5.58|841083668|60.24
2018|1402760000|10.86|7.08|3.78|862700183|61.5
2019|1407745000|10.41|7.09|3.32|882795695|62.71
2020|1411100000|8.52|7.07|1.45|896379022|63.52
2021|1412360000|7.52|7.18|0.34|914094603|64.72
2022|1412175000|6.77|7.37|-0.6|920987153|65.22
2023|1410710000|6.39|7.87|-1.48|924440306|65.53
2024|1408975000|6.77|7.76|-0.99|928439823|65.89
""".strip()


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


def _fallback_wdi_records() -> list[dict[str, Any]]:
    records = []
    for line in FALLBACK_WDI_ROWS.splitlines():
        year, total, birth, death, growth, urban, urban_rate = line.split("|")
        records.append(
            {
                "year": int(year),
                "total_population": int(total),
                "birth_rate": float(birth),
                "death_rate": float(death),
                "natural_growth_rate": float(growth),
                "urban_population": int(urban),
                "urbanization_rate": float(urban_rate),
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
    if os.getenv("POPULATION_INSIGHT_FETCH_WDI", "").strip() == "1":
        try:
            wdi_records = _fetch_wdi_records()
        except Exception:
            wdi_records = _fallback_wdi_records()
    else:
        wdi_records = _fallback_wdi_records()
    if len(wdi_records) < 65:
        wdi_records = _fallback_wdi_records()
    records.extend(
        _decorate_record(
            item,
            "World Bank WDI / official national statistical series",
            "https://api.worldbank.org/v2/country/CHN/indicator",
            "official_cross_checked",
            "1960-2024 indicators from World Bank WDI, cross-referenced to official national statistical source series.",
        )
        for item in wdi_records
    )
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
    history_records = records
    model_records = records
    years = [item["year"] for item in model_records]
    values = [float(item["total_population"]) for item in model_records]
    linear = _linear_regression(years, values)
    latest_year = history_records[-1]["year"]
    future_years = list(range(latest_year + 1, latest_year + forecast_years + 1))
    predictions = []
    for year in future_years:
        predicted = max(0, linear["slope"] * year + linear["intercept"])
        predictions.append({"year": year, "predicted_value": int(round(predicted))})

    return {
        "history": [{"year": item["year"], "value": item["total_population"]} for item in history_records],
        "predictions": predictions,
        "model": {
            "name": "1950-2025 线性趋势",
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
