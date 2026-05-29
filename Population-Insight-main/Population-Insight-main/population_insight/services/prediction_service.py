from __future__ import annotations

import json
import math
import os
from typing import Any
from urllib.request import Request, urlopen

from population_insight.config import METRIC_LABELS
from population_insight.services.population_service import query_population_records

DEFAULT_FORECAST_YEARS = 5


def build_population_prediction(
    region: str,
    metric: str = "total_population",
    forecast_years: int = DEFAULT_FORECAST_YEARS,
) -> dict[str, Any]:
    if metric not in METRIC_LABELS:
        raise ValueError("不支持的预测指标。")

    records = [
        record
        for record in query_population_records({"region": region})
        if record["region"] == region
    ]
    records.sort(key=lambda item: item["year"])
    if len(records) < 3:
        raise ValueError("至少需要 3 年历史数据才能进行趋势预测。")

    forecast_years = max(1, min(int(forecast_years), 10))
    years = [record["year"] for record in records]
    values = [float(record[metric]) for record in records]
    future_years = list(range(years[-1] + 1, years[-1] + forecast_years + 1))

    linear = _linear_regression(years, values)
    growth_rate = _compound_growth_rate(values[0], values[-1], years[-1] - years[0])
    recent_growth_rate = _average_recent_growth(values)

    predictions = []
    for future_year in future_years:
        step = future_year - years[-1]
        linear_value = linear["slope"] * future_year + linear["intercept"]
        growth_value = values[-1] * ((1 + growth_rate) ** step)
        recent_value = values[-1] * ((1 + recent_growth_rate) ** step)
        ensemble_value = linear_value * 0.5 + growth_value * 0.25 + recent_value * 0.25
        predictions.append(
            {
                "year": future_year,
                "linear_value": _round_metric(linear_value, metric),
                "growth_fit_value": _round_metric(growth_value, metric),
                "recent_trend_value": _round_metric(recent_value, metric),
                "predicted_value": _round_metric(max(0, ensemble_value), metric),
            }
        )

    structure = detect_population_structure_changes(records)
    risk = assess_population_risk(records, predictions, metric)
    explanation = explain_prediction_result(
        region=region,
        metric=metric,
        records=records,
        predictions=predictions,
        linear=linear,
        growth_rate=growth_rate,
        recent_growth_rate=recent_growth_rate,
        structure=structure,
        risk=risk,
    )

    return {
        "region": region,
        "metric": metric,
        "metric_label": METRIC_LABELS[metric],
        "history": [{"year": item["year"], "value": item[metric]} for item in records],
        "predictions": predictions,
        "model": {
            "name": "Linear Regression + Growth Rate Ensemble",
            "linear_slope": linear["slope"],
            "linear_intercept": linear["intercept"],
            "r2": linear["r2"],
            "compound_growth_rate": growth_rate,
            "recent_growth_rate": recent_growth_rate,
        },
        "structure": structure,
        "risk": risk,
        "explanation": explanation,
        "chart": build_prediction_chart_payload(records, predictions, metric),
    }


def detect_population_structure_changes(records: list[dict[str, Any]]) -> dict[str, Any]:
    first = records[0]
    latest = records[-1]
    male_ratio_start = _safe_ratio(first["male_population"], first["total_population"]) * 100
    male_ratio_latest = _safe_ratio(latest["male_population"], latest["total_population"]) * 100
    aging_delta = latest["aging_rate"] - first["aging_rate"]
    birth_delta = latest["birth_rate"] - first["birth_rate"]
    urban_delta = latest["urbanization_rate"] - first["urbanization_rate"]

    findings = []
    if aging_delta >= 3:
        findings.append("老龄化率持续上升，人口年龄结构压力增强。")
    elif aging_delta <= -1:
        findings.append("老龄化率有所回落，年龄结构压力阶段性减轻。")
    else:
        findings.append("老龄化率变化较小，年龄结构整体相对平稳。")

    if birth_delta <= -1:
        findings.append("出生率较基期下降，新增人口动能减弱。")
    elif birth_delta >= 1:
        findings.append("出生率较基期上升，新增人口动能有所改善。")

    if abs(male_ratio_latest - male_ratio_start) >= 1:
        findings.append("性别人口占比出现可观察变化，需要结合迁移和出生结构分析。")

    if urban_delta >= 2:
        findings.append("城镇化率提高，人口向城镇集聚趋势明显。")

    return {
        "male_ratio_start": round(male_ratio_start, 2),
        "male_ratio_latest": round(male_ratio_latest, 2),
        "aging_delta": round(aging_delta, 2),
        "birth_delta": round(birth_delta, 2),
        "urbanization_delta": round(urban_delta, 2),
        "findings": findings,
    }


def assess_population_risk(
    records: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    metric: str = "total_population",
) -> dict[str, Any]:
    latest = records[-1]
    if metric == "total_population" and predictions:
        predicted_last = predictions[-1]["predicted_value"]
        population_change = _safe_ratio(predicted_last - latest["total_population"], latest["total_population"]) * 100
    else:
        first = records[0]
        population_change = _safe_ratio(latest["total_population"] - first["total_population"], first["total_population"]) * 100

    factors = []
    score = 0
    if latest["aging_rate"] >= 20:
        score += 35
        factors.append("老龄化率已达到高位。")
    elif latest["aging_rate"] >= 14:
        score += 20
        factors.append("老龄化率处于中高水平。")

    if latest["birth_rate"] < 7:
        score += 25
        factors.append("出生率低于 7%，人口自然补充不足。")
    elif latest["birth_rate"] < 9:
        score += 12
        factors.append("出生率偏低，需要持续观察。")

    if latest["natural_growth_rate"] < 0:
        score += 25
        factors.append("自然增长率为负。")

    if population_change < -1:
        score += 15
        factors.append("预测期末人口规模较当前下降。")
    elif population_change > 5:
        score += 8
        factors.append("预测期末人口增长较快，公共服务承载压力可能上升。")

    score = min(score, 100)
    if score >= 70:
        level = "高"
        suggestion = "建议重点关注养老服务、劳动力供给和生育支持政策。"
    elif score >= 40:
        level = "中"
        suggestion = "建议持续跟踪出生率、老龄化率和人口流动变化。"
    else:
        level = "低"
        suggestion = "当前风险总体可控，保持常规监测即可。"

    return {
        "score": score,
        "level": level,
        "population_change_percent": round(population_change, 2),
        "factors": factors or ["未发现明显高风险因子。"],
        "suggestion": suggestion,
    }


def explain_prediction_result(
    *,
    region: str,
    metric: str,
    records: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    linear: dict[str, float],
    growth_rate: float,
    recent_growth_rate: float,
    structure: dict[str, Any],
    risk: dict[str, Any],
) -> dict[str, str]:
    prompt = _build_llm_prompt(
        region=region,
        metric=metric,
        records=records,
        predictions=predictions,
        linear=linear,
        growth_rate=growth_rate,
        recent_growth_rate=recent_growth_rate,
        structure=structure,
        risk=risk,
    )
    llm_text = _call_optional_llm(prompt)
    if llm_text:
        return {"provider": "llm", "prompt": prompt, "text": llm_text}

    text = _build_local_explanation(region, metric, records, predictions, linear, growth_rate, structure, risk)
    return {"provider": "local-rule", "prompt": prompt, "text": text}


def build_prediction_chart_payload(
    records: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    metric: str,
) -> dict[str, Any]:
    history_years = [record["year"] for record in records]
    future_years = [item["year"] for item in predictions]
    history_values = [record[metric] for record in records]
    predicted_values = [item["predicted_value"] for item in predictions]
    return {
        "title": f"{METRIC_LABELS[metric]}历史趋势与预测",
        "xAxis": history_years + future_years,
        "history": history_values + [None for _ in future_years],
        "prediction": [None for _ in history_years[:-1]] + [history_values[-1]] + predicted_values,
        "metricLabel": METRIC_LABELS[metric],
        "axisUnit": _infer_axis_unit(metric),
        "splitYear": history_years[-1],
    }


def _linear_regression(years: list[int], values: list[float]) -> dict[str, float]:
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(values) / n
    ss_xx = sum((year - mean_x) ** 2 for year in years)
    if ss_xx == 0:
        slope = 0.0
    else:
        slope = sum((year - mean_x) * (value - mean_y) for year, value in zip(years, values)) / ss_xx
    intercept = mean_y - slope * mean_x
    fitted = [slope * year + intercept for year in years]
    ss_tot = sum((value - mean_y) ** 2 for value in values)
    ss_res = sum((value - fit) ** 2 for value, fit in zip(values, fitted))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return {"slope": slope, "intercept": intercept, "r2": max(0.0, min(1.0, r2))}


def _compound_growth_rate(start_value: float, end_value: float, periods: int) -> float:
    if start_value <= 0 or end_value <= 0 or periods <= 0:
        return 0.0
    return (end_value / start_value) ** (1 / periods) - 1


def _average_recent_growth(values: list[float]) -> float:
    rates = []
    for previous, current in zip(values[-4:-1], values[-3:]):
        if previous > 0:
            rates.append((current - previous) / previous)
    if not rates:
        return 0.0
    return sum(rates) / len(rates)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _round_metric(value: float, metric: str) -> int | float:
    if _infer_axis_unit(metric) == "person":
        return int(round(value))
    return round(value, 2)


def _infer_axis_unit(metric: str) -> str:
    if metric in {"total_population", "male_population", "female_population"}:
        return "person"
    if metric in {"birth_rate", "death_rate", "natural_growth_rate", "aging_rate", "urbanization_rate"}:
        return "%"
    return ""


def _build_llm_prompt(**kwargs: Any) -> str:
    region = kwargs["region"]
    metric = kwargs["metric"]
    records = kwargs["records"]
    predictions = kwargs["predictions"]
    linear = kwargs["linear"]
    growth_rate = kwargs["growth_rate"]
    risk = kwargs["risk"]
    latest = records[-1]
    predicted_last = predictions[-1]
    return (
        "你是一名人口趋势分析专家。请基于以下预测结果，输出面向管理者的解释分析，"
        "要求包含趋势判断、风险原因、政策建议，语言简洁。\n"
        f"地区：{region}\n"
        f"指标：{METRIC_LABELS[metric]}\n"
        f"历史年份：{records[0]['year']} 至 {latest['year']}\n"
        f"当前值：{latest[metric]}\n"
        f"预测期末：{predicted_last['year']} 年，预测值 {predicted_last['predicted_value']}\n"
        f"线性回归斜率：{linear['slope']:.4f}，R2：{linear['r2']:.3f}\n"
        f"复合增长率：{growth_rate * 100:.2f}%\n"
        f"风险等级：{risk['level']}，风险得分：{risk['score']}\n"
    )


def _call_optional_llm(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("OPENAI_API_BASE") or os.environ.get("LLM_API_BASE")
    model = os.environ.get("MODEL_NAME") or os.environ.get("LLM_MODEL") or "gpt-4o-mini"
    if not api_key or not api_base:
        return ""

    url = api_base.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = f"{url}/v1/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是严谨的人口数据分析助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urlopen(request, timeout=18) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def _build_local_explanation(
    region: str,
    metric: str,
    records: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    linear: dict[str, float],
    growth_rate: float,
    structure: dict[str, Any],
    risk: dict[str, Any],
) -> str:
    latest = records[-1]
    predicted_last = predictions[-1]
    direction = "上升" if predicted_last["predicted_value"] > latest[metric] else "下降"
    structure_text = "；".join(structure["findings"])
    risk_text = "；".join(risk["factors"])
    return (
        f"{region}{METRIC_LABELS[metric]}预测结果显示，至 {predicted_last['year']} 年该指标预计"
        f"{direction}至 {predicted_last['predicted_value']}。线性回归模型 R2 为 {linear['r2']:.3f}，"
        f"历史复合增长率约为 {growth_rate * 100:.2f}%。结构识别结果：{structure_text}"
        f"智能风险评估为{risk['level']}风险，得分 {risk['score']}，主要原因是：{risk_text}"
        f"建议：{risk['suggestion']}"
    )
