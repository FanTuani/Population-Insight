from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from population_insight.db.connection import fetch_all, fetch_one


BASE_URL = "http://127.0.0.1:5000"
OUT_DIR = ROOT / "output" / "table_evidence"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


TABLES = [
    "users",
    "population_data",
    "operation_logs",
    "regions",
    "data_sources",
    "population_indicators",
    "annual_indicator_values",
    "analysis_reports",
    "national_population_series",
]


PAGE_SHOTS = {
    "users": "/users",
    "population_data": "/records",
    "operation_logs": "/logs",
    "regions": "/regions",
    "data_sources": "/sources",
    "population_indicators": "/indicators",
    "annual_indicator_values": "/indicators",
    "analysis_reports": "/reports",
    "national_population_series": "/national-series",
}


def table_rows(table: str) -> list[dict]:
    order_by = {
        "users": "id ASC",
        "population_data": "id DESC",
        "operation_logs": "id DESC",
        "regions": "id ASC",
        "data_sources": "id ASC",
        "population_indicators": "id ASC",
        "annual_indicator_values": "id DESC",
        "analysis_reports": "id DESC",
        "national_population_series": "year ASC",
    }[table]
    return fetch_all(f"SELECT * FROM {table} ORDER BY {order_by} LIMIT 12")


def table_count(table: str) -> int:
    row = fetch_one(f"SELECT COUNT(*) AS count FROM {table}") or {"count": 0}
    return int(row["count"])


def render_table_html(table: str, rows: list[dict], count: int) -> str:
    if rows:
        columns = list(rows[0].keys())
    else:
        columns = []
    header = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(
            f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns
        ) + "</tr>"
    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <style>
    body {{
      margin: 0;
      padding: 28px;
      font-family: "Microsoft YaHei", "SimSun", sans-serif;
      color: #17242f;
      background: linear-gradient(135deg, #f5f8fb, #edf3f7);
    }}
    .card {{
      background: #fff;
      border: 1px solid #dbe4ec;
      border-radius: 18px;
      box-shadow: 0 16px 36px rgba(30, 55, 70, 0.12);
      overflow: hidden;
    }}
    h1 {{
      margin: 0;
      padding: 22px 24px 6px;
      font-size: 26px;
    }}
    .meta {{
      padding: 0 24px 18px;
      color: #5a6b78;
      font-size: 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    th {{
      background: #0f5f72;
      color: #fff;
      text-align: left;
      padding: 10px;
      white-space: nowrap;
    }}
    td {{
      border-top: 1px solid #e5edf2;
      padding: 8px 10px;
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    tr:nth-child(even) td {{ background: #f7fafc; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>MySQL 表数据展示：{html.escape(table)}</h1>
    <div class="meta">总记录数：{count}；下方展示前 12 条样例数据，用于证明数据已写入 MySQL。</div>
    <table>
      <thead><tr>{header}</tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</body>
</html>
"""


def capture() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
        context = browser.new_context(viewport={"width": 1500, "height": 1050})
        page = context.new_page()

        page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=30_000)
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=30_000)

        for table, route in PAGE_SHOTS.items():
            page.goto(f"{BASE_URL}{route}", wait_until="networkidle", timeout=45_000)
            page.wait_for_timeout(900)
            page.screenshot(path=str(OUT_DIR / f"page_{table}.png"), full_page=True)

        for table in TABLES:
            rows = table_rows(table)
            count = table_count(table)
            page.set_content(render_table_html(table, rows, count), wait_until="networkidle")
            page.screenshot(path=str(OUT_DIR / f"db_{table}.png"), full_page=True)

        browser.close()

    print(OUT_DIR)


if __name__ == "__main__":
    capture()
