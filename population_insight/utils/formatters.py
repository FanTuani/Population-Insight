from __future__ import annotations

from typing import Any

DISPLAY_FIELDS = [
    ("id", "ID"),
    ("region", "地区"),
    ("year", "年份"),
    ("total_population", "总人口"),
    ("male_population", "男性人口"),
    ("female_population", "女性人口"),
    ("birth_rate", "出生率"),
    ("death_rate", "死亡率"),
    ("natural_growth_rate", "自然增长率"),
    ("aging_rate", "老龄化率"),
    ("urbanization_rate", "城镇化率"),
    ("remarks", "备注"),
]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def records_to_table(records: list[dict[str, Any]], fields: list[tuple[str, str]] | None = None) -> str:
    if not records:
        return "暂无数据。"

    fields = fields or DISPLAY_FIELDS
    widths = []
    for key, label in fields:
        content_width = max(len(_stringify(row.get(key, ""))) for row in records)
        widths.append(max(len(label), content_width))

    header = " | ".join(label.ljust(width) for (_, label), width in zip(fields, widths))
    separator = "-+-".join("-" * width for width in widths)
    rows = []
    for row in records:
        row_text = " | ".join(
            _stringify(row.get(key, "")).ljust(width)
            for (key, _), width in zip(fields, widths)
        )
        rows.append(row_text)
    return "\n".join([header, separator, *rows])


def statistics_to_lines(statistics: dict[str, Any]) -> str:
    lines = [
        f"记录数量：{statistics['record_count']}",
        f"平均总人口：{statistics['avg_total_population']:.2f}",
        f"平均出生率：{statistics['avg_birth_rate']:.2f}",
        f"平均老龄化率：{statistics['avg_aging_rate']:.2f}",
        (
            f"最高总人口：{statistics['max_population']['region']} "
            f"{statistics['max_population']['year']}年 "
            f"({statistics['max_population']['total_population']})"
        ),
        (
            f"最低总人口：{statistics['min_population']['region']} "
            f"{statistics['min_population']['year']}年 "
            f"({statistics['min_population']['total_population']})"
        ),
    ]

    if statistics["growth_summary"]:
        lines.append("地区增长率：")
        for item in statistics["growth_summary"]:
            lines.append(
                f"  {item['region']}：{item['start_year']} -> {item['end_year']}，增长 {item['growth_percent']:.2f}%"
            )
    return "\n".join(lines)
