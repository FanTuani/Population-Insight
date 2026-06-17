from __future__ import annotations

import html
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT_DIR / "output" / "automated_tests" / "latest"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
TMP_DIR = ROOT_DIR / ".tmp" / "acceptance"
TEST_DB_PATH = TMP_DIR / "acceptance_population_insight.db"
TEST_OUTPUT_DIR = TMP_DIR / "output"
JUNIT_PATH = REPORT_DIR / "pytest-junit.xml"
PYTEST_LOG_PATH = REPORT_DIR / "pytest-output.txt"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


@dataclass
class ScreenshotResult:
    label: str
    path: Path


def main() -> int:
    started_at = datetime.now()
    prepare_directories()
    env = build_test_env()

    checks: list[CheckResult] = []
    screenshots: list[ScreenshotResult] = []

    precheck_ok = run_prechecks(checks)
    pytest_code = run_pytest(env, checks) if precheck_ok else 1
    pytest_summary = parse_junit_summary(JUNIT_PATH)

    browser_code = 1
    server = None
    base_url = ""
    if precheck_ok:
        port = find_free_port()
        base_url = f"http://127.0.0.1:{port}"
        server = start_server(port, env, checks)
        try:
            if wait_for_server(base_url, checks):
                browser_code = run_browser_checks(base_url, screenshots, checks)
        finally:
            stop_server(server)

    report_path = write_html_report(
        started_at=started_at,
        base_url=base_url,
        pytest_summary=pytest_summary,
        checks=checks,
        screenshots=screenshots,
    )

    print(f"验收测试报告: {report_path}")
    if pytest_code == 0 and browser_code == 0:
        return 0
    return 1


def prepare_directories() -> None:
    if REPORT_DIR.exists():
        shutil.rmtree(REPORT_DIR)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-shm", "-wal", "-journal"):
        path = Path(f"{TEST_DB_PATH}{suffix}")
        if path.exists():
            path.unlink()


def build_test_env() -> dict[str, str]:
    env = os.environ.copy()
    env["POPULATION_INSIGHT_DB_ENGINE"] = "sqlite"
    env["POPULATION_INSIGHT_DB_PATH"] = str(TEST_DB_PATH)
    env["POPULATION_INSIGHT_OUTPUT_DIR"] = str(TEST_OUTPUT_DIR)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run_prechecks(checks: list[CheckResult]) -> bool:
    required_modules = ["flask", "pytest", "playwright"]
    ok = True
    for module in required_modules:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module}; print('ok')"],
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            checks.append(CheckResult(f"依赖检查: {module}", "PASS", "模块可导入"))
        else:
            ok = False
            checks.append(
                CheckResult(
                    f"依赖检查: {module}",
                    "FAIL",
                    f"无法导入，请先安装依赖: {result.stderr.strip() or result.stdout.strip()}",
                )
            )
    return ok


def run_pytest(env: dict[str, str], checks: list[CheckResult]) -> int:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-q",
        f"--junitxml={JUNIT_PATH}",
        "--cov=population_insight",
        "--cov=app",
        "--cov-report=term-missing",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        capture_output=True,
    )
    PYTEST_LOG_PATH.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    status = "PASS" if result.returncode == 0 else "FAIL"
    checks.append(CheckResult("pytest 回归测试", status, f"退出码 {result.returncode}，日志见 {PYTEST_LOG_PATH}"))
    return result.returncode


def parse_junit_summary(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    if root.tag == "testsuites":
        tests = sum(int(item.attrib.get("tests", 0)) for item in root)
        failures = sum(int(item.attrib.get("failures", 0)) for item in root)
        errors = sum(int(item.attrib.get("errors", 0)) for item in root)
        skipped = sum(int(item.attrib.get("skipped", 0)) for item in root)
        return {"tests": tests, "failures": failures, "errors": errors, "skipped": skipped}
    return {
        "tests": int(root.attrib.get("tests", 0)),
        "failures": int(root.attrib.get("failures", 0)),
        "errors": int(root.attrib.get("errors", 0)),
        "skipped": int(root.attrib.get("skipped", 0)),
    }


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_server(port: int, env: dict[str, str], checks: list[CheckResult]) -> subprocess.Popen:
    command = [
        sys.executable,
        "-c",
        (
            "from app import create_app; "
            f"create_app().run(host='127.0.0.1', port={port}, debug=False, use_reloader=False)"
        ),
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    checks.append(CheckResult("Flask 测试服务", "INFO", f"已启动，PID={process.pid}"))
    return process


def wait_for_server(base_url: str, checks: list[CheckResult]) -> bool:
    deadline = time.time() + 20
    last_error = ""
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/login", timeout=2) as response:
                if response.status == 200:
                    checks.append(CheckResult("Flask 服务健康检查", "PASS", f"{base_url}/login 返回 200"))
                    return True
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = str(error)
        time.sleep(0.5)
    checks.append(CheckResult("Flask 服务健康检查", "FAIL", last_error or "服务未在 20 秒内就绪"))
    return False


def run_browser_checks(
    base_url: str,
    screenshots: list[ScreenshotResult],
    checks: list[CheckResult],
) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        checks.append(CheckResult("Playwright 浏览器检查", "FAIL", f"无法导入 Playwright: {error}"))
        return 1

    pages = [
        ("登录页", "/login", "登录"),
        ("仪表盘", "/", "全国人口趋势分析总览"),
        ("数据管理页", "/records", "人口数据管理"),
        ("数据采集页", "/collection", "数据采集"),
        ("统计分析页", "/statistics", "统计分析"),
        ("对比分析页", "/comparison", "数据对比"),
        ("趋势预测页", "/prediction", "趋势预测"),
        ("全国长序列页", "/national-series", "全国长序列"),
        ("图表中心页", "/charts", "图表中心"),
        ("预警分析页", "/alerts", "预警分析"),
        ("报告页", "/reports", "分析报告"),
    ]

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})

            page.goto(f"{base_url}/login", wait_until="networkidle")
            take_screenshot(page, "登录页", "01-login.png", screenshots)
            page.fill('input[name="username"]', "admin")
            page.fill('input[name="password"]', "admin123")
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            if page.url.rstrip("/") != base_url:
                raise AssertionError(f"登录后 URL 异常: {page.url}")

            for index, (label, path, expected_text) in enumerate(pages[1:], start=2):
                page.goto(f"{base_url}{path}", wait_until="networkidle")
                content = page.locator("body").inner_text(timeout=5000)
                if expected_text not in content:
                    raise AssertionError(f"{label} 未找到关键文本: {expected_text}")
                take_screenshot(page, label, f"{index:02d}-{slugify(label)}.png", screenshots)

            browser.close()
        checks.append(CheckResult("Playwright 浏览器检查", "PASS", f"已保存 {len(screenshots)} 张截图"))
        return 0
    except Exception as error:  # noqa: BLE001 - report generation should keep running.
        checks.append(
            CheckResult(
                "Playwright 浏览器检查",
                "FAIL",
                f"{error}。若提示 browser executable 缺失，请运行: python -m playwright install chromium",
            )
        )
        return 1


def take_screenshot(page, label: str, filename: str, screenshots: list[ScreenshotResult]) -> None:
    path = SCREENSHOT_DIR / filename
    page.screenshot(path=str(path), full_page=True)
    screenshots.append(ScreenshotResult(label=label, path=path))


def slugify(value: str) -> str:
    mapping = {
        "仪表盘": "dashboard",
        "数据管理页": "records",
        "数据采集页": "collection",
        "统计分析页": "statistics",
        "对比分析页": "comparison",
        "趋势预测页": "prediction",
        "全国长序列页": "national-series",
        "图表中心页": "charts",
        "预警分析页": "alerts",
        "报告页": "reports",
    }
    return mapping.get(value, "page")


def stop_server(process: subprocess.Popen | None) -> None:
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def write_html_report(
    *,
    started_at: datetime,
    base_url: str,
    pytest_summary: dict[str, int],
    checks: list[CheckResult],
    screenshots: list[ScreenshotResult],
) -> Path:
    duration = datetime.now() - started_at
    passed = sum(1 for item in checks if item.status == "PASS")
    failed = sum(1 for item in checks if item.status == "FAIL")
    report_path = REPORT_DIR / "index.html"
    rows = "\n".join(
        f"<tr><td>{html.escape(item.name)}</td><td class='{item.status.lower()}'>{item.status}</td>"
        f"<td>{html.escape(item.detail)}</td></tr>"
        for item in checks
    )
    gallery = "\n".join(
        "<figure>"
        f"<img src='screenshots/{html.escape(item.path.name)}' alt='{html.escape(item.label)}'>"
        f"<figcaption>{html.escape(item.label)}</figcaption>"
        "</figure>"
        for item in screenshots
    )
    log_excerpt = ""
    if PYTEST_LOG_PATH.exists():
        text = PYTEST_LOG_PATH.read_text(encoding="utf-8", errors="ignore")
        log_excerpt = html.escape(text[-6000:])

    report_path.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Population-Insight 自动化验收报告</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f8fb; color: #172033; }}
    header {{ padding: 32px 40px; background: #0f766e; color: white; }}
    main {{ padding: 28px 40px 48px; }}
    h1, h2 {{ margin: 0 0 14px; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 24px 0; }}
    .card, table, pre, figure {{ background: white; border: 1px solid #dbe4ef; border-radius: 8px; box-shadow: 0 1px 2px rgba(15, 23, 42, .05); }}
    .card {{ padding: 18px; }}
    .card span {{ color: #64748b; font-size: 13px; }}
    .card strong {{ display: block; margin-top: 8px; font-size: 24px; }}
    table {{ border-collapse: collapse; width: 100%; overflow: hidden; }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid #e5edf5; text-align: left; vertical-align: top; }}
    th {{ background: #eef6f5; }}
    .pass {{ color: #047857; font-weight: 700; }}
    .fail {{ color: #b91c1c; font-weight: 700; }}
    .info {{ color: #1d4ed8; font-weight: 700; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px; }}
    figure {{ margin: 0; padding: 10px; }}
    img {{ display: block; width: 100%; border-radius: 6px; border: 1px solid #e2e8f0; }}
    figcaption {{ margin-top: 8px; font-weight: 700; }}
    pre {{ padding: 16px; overflow: auto; white-space: pre-wrap; max-height: 420px; }}
  </style>
</head>
<body>
  <header>
    <h1>Population-Insight 自动化验收报告</h1>
    <p>生成时间：{html.escape(started_at.strftime("%Y-%m-%d %H:%M:%S"))}</p>
  </header>
  <main>
    <section class="summary">
      <div class="card"><span>检查通过</span><strong>{passed}</strong></div>
      <div class="card"><span>检查失败</span><strong>{failed}</strong></div>
      <div class="card"><span>pytest 用例</span><strong>{pytest_summary["tests"]}</strong></div>
      <div class="card"><span>pytest 失败/错误</span><strong>{pytest_summary["failures"] + pytest_summary["errors"]}</strong></div>
      <div class="card"><span>截图数量</span><strong>{len(screenshots)}</strong></div>
      <div class="card"><span>运行耗时</span><strong>{str(duration).split(".")[0]}</strong></div>
    </section>
    <section>
      <h2>运行环境</h2>
      <table>
        <tr><th>测试数据库</th><td>{html.escape(str(TEST_DB_PATH))}</td></tr>
        <tr><th>测试服务</th><td>{html.escape(base_url or "未启动")}</td></tr>
        <tr><th>报告目录</th><td>{html.escape(str(REPORT_DIR))}</td></tr>
      </table>
    </section>
    <section>
      <h2>检查结果</h2>
      <table>
        <thead><tr><th>检查项</th><th>状态</th><th>说明</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>演示截图</h2>
      <div class="gallery">{gallery or "<p>未生成截图。</p>"}</div>
    </section>
    <section>
      <h2>pytest 输出摘要</h2>
      <pre>{log_excerpt}</pre>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return report_path


if __name__ == "__main__":
    raise SystemExit(main())
