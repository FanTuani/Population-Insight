from __future__ import annotations

import csv
import io
import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from population_insight.services.population_service import add_population_record

REQUIRED_FIELDS = {
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

HEADER_ALIASES = {
    "region": {"地区", "区域", "省份", "城市", "行政区", "region", "area", "name"},
    "year": {"年份", "年度", "year"},
    "total_population": {"总人口", "常住人口", "年末常住人口", "人口总数", "total_population", "population"},
    "male_population": {"男性人口", "男性", "男", "男常住人口", "male_population", "male"},
    "female_population": {"女性人口", "女性", "女", "女常住人口", "female_population", "female"},
    "birth_rate": {"出生率", "人口出生率", "birth_rate", "birth rate"},
    "death_rate": {"死亡率", "人口死亡率", "death_rate", "death rate"},
    "aging_rate": {"老龄化率", "老年人口占比", "60岁及以上占比", "60岁以上占比", "aging_rate", "aging rate"},
    "urbanization_rate": {"城镇化率", "常住人口城镇化率", "urbanization_rate", "urbanization rate"},
    "remarks": {"备注", "说明", "数据说明", "remarks", "note"},
}


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._current_table = []
        elif tag == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            text = " ".join(part.strip() for part in self._current_cell if part.strip())
            self._current_row.append(_squash_space(text))
            self._current_cell = None
        elif tag == "tr" and self._current_table is not None and self._current_row is not None:
            if any(cell for cell in self._current_row):
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._current_table is not None:
            if self._current_table:
                self.tables.append(self._current_table)
            self._current_table = None


def fetch_public_population_source(url: str, timeout: int = 12) -> dict[str, Any]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("请输入有效的 http 或 https 公开数据地址。")

    request = Request(
        url,
        headers={
            "User-Agent": "Population-Insight/1.0 (+https://localhost)",
            "Accept": "text/html,text/plain,text/csv,*/*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read(2_000_000)
        charset = response.headers.get_content_charset() or "utf-8"
        content_type = response.headers.get("Content-Type", "")

    text = _decode_body(body, charset)
    records = parse_population_records(text)
    return {
        "url": url,
        "content_type": content_type,
        "record_count": len(records),
        "records": records,
    }


def collect_population_records(raw_text: str = "", source_url: str = "") -> dict[str, Any]:
    if source_url.strip():
        return fetch_public_population_source(source_url)

    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("请提供公开数据链接，或粘贴包含人口字段的表格文本。")

    records = parse_population_records(raw_text)
    return {
        "url": "",
        "content_type": "manual-text",
        "record_count": len(records),
        "records": records,
    }


def parse_population_records(raw_text: str) -> list[dict[str, Any]]:
    table_rows = _extract_html_tables(raw_text)
    records = _records_from_tables(table_rows)
    if records:
        return records

    records = _records_from_delimited_text(raw_text)
    if records:
        return records

    raise ValueError("未能从内容中识别人口数据表，请确认表头包含地区、年份、总人口、性别人口、出生率等字段。")


def encode_records(records: list[dict[str, Any]]) -> str:
    return json.dumps(records, ensure_ascii=False)


def decode_records(payload: str) -> list[dict[str, Any]]:
    try:
        records = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError("采集结果已失效，请重新预览后再导入。") from error
    if not isinstance(records, list):
        raise ValueError("采集结果格式不正确，请重新预览后再导入。")
    return records


def import_collected_records(records: list[dict[str, Any]], username: str) -> dict[str, Any]:
    imported = 0
    errors: list[str] = []
    for index, record in enumerate(records, start=1):
        try:
            add_population_record(record, username=username)
            imported += 1
        except ValueError as error:
            errors.append(f"第 {index} 行：{error}")
    return {"imported": imported, "failed": len(errors), "errors": errors}


def _decode_body(body: bytes, charset: str) -> str:
    for candidate in (charset, "utf-8", "gb18030"):
        try:
            return body.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="ignore")


def _extract_html_tables(raw_text: str) -> list[list[list[str]]]:
    if "<table" not in raw_text.lower():
        return []
    parser = _TableParser()
    parser.feed(raw_text)
    return parser.tables


def _records_from_tables(tables: list[list[list[str]]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in tables:
        if len(table) < 2:
            continue
        header_index = _find_header_row(table)
        if header_index is None:
            continue
        headers = table[header_index]
        for row in table[header_index + 1:]:
            item = _normalize_row(headers, row)
            if item:
                records.append(item)
    return records


def _records_from_delimited_text(raw_text: str) -> list[dict[str, Any]]:
    sample = raw_text.strip()
    for delimiter in (",", "\t", "|", ";"):
        if delimiter not in sample:
            continue
        reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if len(rows) < 2:
            continue
        records = [
            item
            for item in (_normalize_row(rows[0], row) for row in rows[1:])
            if item is not None
        ]
        if records:
            return records
    return []


def _normalize_row(headers: list[str], row: list[str]) -> dict[str, Any] | None:
    mapped: dict[str, tuple[str, str]] = {}
    for index, header in enumerate(headers):
        field = _match_field(header)
        if field and index < len(row):
            mapped[field] = (header, row[index])

    if not REQUIRED_FIELDS.issubset(mapped):
        return None

    normalized: dict[str, Any] = {
        "region": _clean_value(mapped["region"][1]),
        "year": _parse_year(mapped["year"][1]),
        "total_population": _parse_population(mapped["total_population"][1], mapped["total_population"][0]),
        "male_population": _parse_population(mapped["male_population"][1], mapped["male_population"][0]),
        "female_population": _parse_population(mapped["female_population"][1], mapped["female_population"][0]),
        "birth_rate": _parse_rate(mapped["birth_rate"][1]),
        "death_rate": _parse_rate(mapped["death_rate"][1]),
        "aging_rate": _parse_rate(mapped["aging_rate"][1]),
        "urbanization_rate": _parse_rate(mapped["urbanization_rate"][1]),
        "remarks": _clean_value(mapped.get("remarks", ("", ""))[1]),
    }
    if not normalized["remarks"]:
        normalized["remarks"] = "公开数据采集导入"
    return normalized


def _find_header_row(table: list[list[str]]) -> int | None:
    for index, row in enumerate(table[:4]):
        matched_fields = {_match_field(cell) for cell in row}
        if REQUIRED_FIELDS.issubset({field for field in matched_fields if field}):
            return index
    return None


def _match_field(header: str) -> str | None:
    normalized = _normalize_header(header)
    normalized_aliases = {
        field: {_normalize_header(alias) for alias in aliases}
        for field, aliases in HEADER_ALIASES.items()
    }
    for field, aliases in normalized_aliases.items():
        if normalized in aliases:
            return field

    for field, aliases in HEADER_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            alias_key = _normalize_header(alias)
            if not alias_key or len(alias_key) < 3:
                continue
            if alias_key == "population" and any(prefix in normalized for prefix in {"male", "female"}):
                continue
            if alias_key in normalized:
                return field
    return None


def _normalize_header(value: str) -> str:
    return re.sub(r"[\s_（）()\[\]【】:：/%‰]+", "", str(value).lower())


def _squash_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_value(value: Any) -> str:
    return _squash_space(str(value or "").replace("\xa0", " "))


def _parse_year(value: Any) -> int:
    match = re.search(r"(19|20)\d{2}", str(value))
    if not match:
        raise ValueError("采集数据中存在无法识别的年份。")
    return int(match.group(0))


def _parse_number(value: Any) -> float:
    text = str(value or "").replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        raise ValueError(f"无法识别数值：{value}")
    return float(match.group(0))


def _parse_population(value: Any, header: str = "") -> int:
    number = _parse_number(value)
    unit_text = f"{header} {value}"
    if "亿" in unit_text:
        number *= 100_000_000
    elif "万" in unit_text:
        number *= 10_000
    return int(round(number))


def _parse_rate(value: Any) -> float:
    return round(_parse_number(value), 2)
