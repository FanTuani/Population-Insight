from __future__ import annotations

from typing import Any

from population_insight.config import YEAR_MAX, YEAR_MIN


def ensure_text(value: Any, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name}不能为空。")
    return text


def ensure_year(value: Any) -> int:
    try:
        year = int(str(value).strip())
    except (TypeError, ValueError) as error:
        raise ValueError("年份必须是整数。") from error

    if year < YEAR_MIN or year > YEAR_MAX:
        raise ValueError(f"年份必须在 {YEAR_MIN} 到 {YEAR_MAX} 之间。")
    return year


def ensure_non_negative_number(
    value: Any, field_name: str, integer: bool = False
) -> int | float:
    try:
        number = int(str(value).strip()) if integer else float(str(value).strip())
    except (TypeError, ValueError) as error:
        expected = "整数" if integer else "数字"
        raise ValueError(f"{field_name}必须是有效{expected}。") from error

    if number < 0:
        raise ValueError(f"{field_name}不能为负数。")
    return number


def _parse_optional_field(
    source: dict[str, Any], field: str, field_name: str, integer: bool = False
) -> int | float | str | None:
    if field not in source:
        return None

    value = source[field]
    if isinstance(value, str) and not value.strip():
        return None

    if field == "region":
        return ensure_text(value, field_name)
    if field == "year":
        return ensure_year(value)
    if field in {
        "remarks",
        "aging_rate_basis",
        "data_source_name",
        "source_url",
        "data_quality",
    }:
        return str(value).strip()
    return ensure_non_negative_number(value, field_name, integer=integer)


def validate_population_payload(
    data: dict[str, Any],
    partial: bool = False,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields = {
        "region": {"label": "地区", "integer": False},
        "year": {"label": "年份", "integer": True},
        "total_population": {"label": "总人口", "integer": True},
        "male_population": {"label": "男性人口", "integer": True},
        "female_population": {"label": "女性人口", "integer": True},
        "birth_rate": {"label": "出生率", "integer": False},
        "death_rate": {"label": "死亡率", "integer": False},
        "aging_rate": {"label": "老龄化率", "integer": False},
        "urbanization_rate": {"label": "城镇化率", "integer": False},
        "aging_rate_basis": {"label": "老龄化口径", "integer": False},
        "data_source_name": {"label": "数据来源名称", "integer": False},
        "source_url": {"label": "来源链接", "integer": False},
        "data_quality": {"label": "数据质量", "integer": False},
        "remarks": {"label": "备注", "integer": False},
    }

    required_fields = {
        "region",
        "year",
        "total_population",
        "male_population",
        "female_population",
        "birth_rate",
        "death_rate",
        "aging_rate",
        "urbanization_rate",
    }

    normalized: dict[str, Any] = {}
    merged = dict(existing or {})

    for field, meta in fields.items():
        parsed = _parse_optional_field(data, field, meta["label"], meta["integer"])
        if parsed is None:
            continue
        normalized[field] = parsed
        merged[field] = parsed

    if not partial:
        missing_fields = [field for field in required_fields if field not in normalized]
        if missing_fields:
            labels = [fields[field]["label"] for field in missing_fields]
            raise ValueError(f"缺少必填字段：{'、'.join(labels)}。")

    if required_fields.issubset(merged):
        total_population = int(merged["total_population"])
        male_population = int(merged["male_population"])
        female_population = int(merged["female_population"])

        if male_population + female_population != total_population:
            raise ValueError("男性人口与女性人口之和必须等于总人口。")

    if "birth_rate" in merged and "death_rate" in merged:
        normalized["natural_growth_rate"] = round(
            float(merged["birth_rate"]) - float(merged["death_rate"]), 2
        )

    if partial and not normalized:
        raise ValueError("没有可更新的字段。")

    return normalized
