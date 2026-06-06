from __future__ import annotations

import sqlite3
from typing import Any

from population_insight.config import ALLOWED_SORT_FIELDS
from population_insight.db.connection import fetch_all, fetch_one, get_connection
from population_insight.services.log_service import log_operation
from population_insight.utils.validators import validate_population_payload

REGION_PINYIN_ORDER = {
    "安徽省": "anhui",
    "北京市": "beijing",
    "重庆市": "chongqing",
    "福建省": "fujian",
    "甘肃省": "gansu",
    "广东省": "guangdong",
    "广西壮族自治区": "guangxi",
    "贵州省": "guizhou",
    "海南省": "hainan",
    "河北省": "hebei",
    "河南省": "henan",
    "黑龙江省": "heilongjiang",
    "湖北省": "hubei",
    "湖南省": "hunan",
    "吉林省": "jilin",
    "江苏省": "jiangsu",
    "江西省": "jiangxi",
    "辽宁省": "liaoning",
    "内蒙古自治区": "neimenggu",
    "宁夏回族自治区": "ningxia",
    "青海省": "qinghai",
    "山东省": "shandong",
    "山西省": "shanxi",
    "陕西省": "shaanxi",
    "上海市": "shanghai",
    "四川省": "sichuan",
    "天津市": "tianjin",
    "西藏自治区": "xizang",
    "新疆维吾尔自治区": "xinjiang",
    "云南省": "yunnan",
    "浙江省": "zhejiang",
    "全国": "quanguo",
}

INSERT_FIELDS = [
    "region",
    "year",
    "total_population",
    "male_population",
    "female_population",
    "birth_rate",
    "death_rate",
    "natural_growth_rate",
    "aging_rate",
    "urbanization_rate",
    "aging_rate_basis",
    "data_source_name",
    "source_url",
    "data_quality",
    "remarks",
]


def add_population_record(data_dict: dict[str, Any], username: str = "system") -> int:
    normalized = validate_population_payload(data_dict)
    values = [normalized.get(field, "") for field in INSERT_FIELDS]

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                f"""
                INSERT INTO population_data ({", ".join(INSERT_FIELDS)})
                VALUES ({", ".join("?" for _ in INSERT_FIELDS)})
                """,
                values,
            )
            connection.commit()
            record_id = cursor.lastrowid
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            raise ValueError("同一地区同一年份的数据已存在。") from error
        raise ValueError("新增数据失败，请检查输入内容。") from error

    log_operation(username, "ADD_RECORD", target_id=record_id, details=normalized["region"])
    return record_id


def get_population_record_by_id(record_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT *
        FROM population_data
        WHERE id = ?
        """,
        (record_id,),
    )


def query_population_records(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    query = ["SELECT * FROM population_data WHERE 1 = 1"]
    params: list[Any] = []

    if filters.get("region"):
        query.append("AND region LIKE ?")
        params.append(f"%{str(filters['region']).strip()}%")
    if filters.get("year"):
        query.append("AND year = ?")
        params.append(int(filters["year"]))
    if filters.get("start_year"):
        query.append("AND year >= ?")
        params.append(int(filters["start_year"]))
    if filters.get("end_year"):
        query.append("AND year <= ?")
        params.append(int(filters["end_year"]))

    range_filters = {
        "min_total_population": ("total_population", ">="),
        "max_total_population": ("total_population", "<="),
        "min_birth_rate": ("birth_rate", ">="),
        "max_birth_rate": ("birth_rate", "<="),
        "min_aging_rate": ("aging_rate", ">="),
        "max_aging_rate": ("aging_rate", "<="),
    }
    for key, (column, operator) in range_filters.items():
        if filters.get(key) in (None, ""):
            continue
        query.append(f"AND {column} {operator} ?")
        params.append(float(filters[key]))

    query.append("ORDER BY region ASC, year ASC")
    return fetch_all(" ".join(query), params)


def update_population_record(
    record_id: int, updates: dict[str, Any], username: str = "system"
) -> None:
    existing = get_population_record_by_id(record_id)
    if not existing:
        raise ValueError("要修改的记录不存在。")

    normalized = validate_population_payload(updates, partial=True, existing=existing)
    assignments = [f"{field} = ?" for field in normalized]
    values = list(normalized.values())
    values.append(record_id)

    try:
        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE population_data
                SET {", ".join(assignments)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                values,
            )
            connection.commit()
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            raise ValueError("修改后会与已有地区年份记录冲突。") from error
        raise ValueError("修改数据失败。") from error

    log_operation(username, "UPDATE_RECORD", target_id=record_id, details=existing["region"])


def delete_population_record(record_id: int, username: str = "system") -> None:
    existing = get_population_record_by_id(record_id)
    if not existing:
        raise ValueError("要删除的记录不存在。")

    with get_connection() as connection:
        connection.execute("DELETE FROM population_data WHERE id = ?", (record_id,))
        connection.commit()

    log_operation(username, "DELETE_RECORD", target_id=record_id, details=existing["region"])


def sort_population_records(
    records: list[dict[str, Any]], field: str, order: str = "asc"
) -> list[dict[str, Any]]:
    field = ALLOWED_SORT_FIELDS.get(field, field)
    if field not in ALLOWED_SORT_FIELDS.values():
        raise ValueError("不支持的排序字段。")

    reverse = order.lower() == "desc"
    if field == "region":
        return sorted(records, key=lambda item: _region_sort_key(item.get("region", "")), reverse=reverse)
    return sorted(records, key=lambda item: item.get(field), reverse=reverse)


def get_distinct_regions() -> list[str]:
    rows = fetch_all("SELECT DISTINCT region FROM population_data")
    return sorted([row["region"] for row in rows], key=_region_sort_key)


def get_analysis_regions(include_national: bool = True) -> list[str]:
    regions = get_distinct_regions()
    if include_national and "全国" not in regions:
        regions.append("全国")
    return sorted(regions, key=_region_sort_key)


def get_distinct_years() -> list[int]:
    rows = fetch_all("SELECT DISTINCT year FROM population_data ORDER BY year ASC")
    return [row["year"] for row in rows]


def _region_sort_key(region: str) -> tuple[str, str]:
    return (REGION_PINYIN_ORDER.get(region, region), region)
