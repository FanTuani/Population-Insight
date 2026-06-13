from __future__ import annotations

import html
import math
import sqlite3
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "ppt"
PREVIEW_DIR = OUT_DIR / "previews"
PPTX_PATH = OUT_DIR / "Population-Insight-答辩汇报.pptx"
CONTACT_SHEET_PATH = OUT_DIR / "contact_sheet.png"

SLIDE_W = 13.333333
SLIDE_H = 7.5
EMU_PER_IN = 914400
PX_W = 1600
PX_H = 900
SX = PX_W / SLIDE_W
SY = PX_H / SLIDE_H

BG = "F6F8F6"
INK = "1E2A29"
MUTED = "5E6B68"
GREEN = "2F7D62"
GREEN_DARK = "1F5E49"
MINT = "DCEFE7"
BLUE = "356C9B"
BLUE_SOFT = "DDEAF5"
GOLD = "B7892B"
GOLD_SOFT = "F4E8C9"
RED = "B45B5B"
RED_SOFT = "F1DCDC"
WHITE = "FFFFFF"
LINE = "C7D4CF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


@dataclass
class Element:
    kind: str
    x: float
    y: float
    w: float
    h: float
    text: str = ""
    fill: str = WHITE
    line: str = LINE
    color: str = INK
    font_size: int = 18
    bold: bool = False
    radius: bool = True
    align: str = "left"
    valign: str = "top"
    shape: str = "roundRect"
    arrow: bool = False
    weight: int = 1


@dataclass
class Slide:
    title: str
    section: str
    elements: list[Element] = field(default_factory=list)
    notes: str = ""

    def add(self, element: Element) -> None:
        self.elements.append(element)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def emu(value: float) -> int:
    return int(round(value * EMU_PER_IN))


def rgb(value: str) -> tuple[int, int, int]:
    value = value.strip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def px_rect(e: Element) -> tuple[int, int, int, int]:
    return int(e.x * SX), int(e.y * SY), int((e.x + e.w) * SX), int((e.y + e.h) * SY)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            candidate = current + ch
            if draw.textbbox((0, 0), candidate, font=fnt)[2] <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = ch
        lines.append(current)
    return lines


def draw_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, size: int, color: str, bold: bool, align: str, valign: str) -> None:
    fnt = font(size, bold)
    x1, y1, x2, y2 = box
    pad = max(10, size // 2)
    lines = wrap_text(draw, text, fnt, x2 - x1 - pad * 2)
    line_h = int(size * 1.38)
    total_h = len(lines) * line_h
    if valign == "mid":
        y = y1 + (y2 - y1 - total_h) // 2
    elif valign == "bottom":
        y = y2 - total_h - pad
    else:
        y = y1 + pad
    for line in lines:
        tw = draw.textbbox((0, 0), line, font=fnt)[2]
        if align == "center":
            x = x1 + (x2 - x1 - tw) // 2
        elif align == "right":
            x = x2 - tw - pad
        else:
            x = x1 + pad
        draw.text((x, y), line, font=fnt, fill=rgb(color))
        y += line_h


def slide_chrome(slide: Slide, idx: int) -> None:
    slide.add(Element("rect", 0, 0, SLIDE_W, SLIDE_H, fill=BG, line=BG, radius=False, shape="rect"))
    slide.add(Element("rect", 0, 0, 0.16, SLIDE_H, fill=GREEN_DARK, line=GREEN_DARK, radius=False, shape="rect"))
    slide.add(Element("text", 0.55, 0.28, 1.2, 0.28, slide.section, fill=BG, line=BG, color=GREEN, font_size=10, bold=True, shape="rect"))
    slide.add(Element("text", 11.7, 7.03, 1.0, 0.25, f"{idx:02d}", fill=BG, line=BG, color=MUTED, font_size=10, align="right", shape="rect"))


def pill(slide: Slide, x: float, y: float, w: float, text: str, fill: str = MINT, color: str = GREEN_DARK) -> None:
    slide.add(Element("text", x, y, w, 0.32, text, fill=fill, line=fill, color=color, font_size=10, bold=True, align="center", valign="mid"))


def card(slide: Slide, x: float, y: float, w: float, h: float, title: str, body: str, fill: str = WHITE, accent: str = GREEN) -> None:
    slide.add(Element("rect", x, y, w, h, fill=fill, line=LINE))
    slide.add(Element("rect", x, y, 0.08, h, fill=accent, line=accent, radius=False, shape="rect"))
    if h < 0.85:
        slide.add(Element("text", x + 0.18, y + 0.1, w - 0.34, h - 0.18, title, fill=fill, line=fill, color=INK, font_size=11, bold=True, shape="rect"))
        return
    slide.add(Element("text", x + 0.18, y + 0.14, w - 0.34, 0.35, title, fill=fill, line=fill, color=INK, font_size=14, bold=True, shape="rect"))
    slide.add(Element("text", x + 0.18, y + 0.54, w - 0.34, max(0.2, h - 0.64), body, fill=fill, line=fill, color=MUTED, font_size=10, shape="rect"))


def db_stats() -> dict[str, int | str]:
    path = ROOT / "data" / "population_insight.db"
    with sqlite3.connect(path) as con:
        cur = con.cursor()
        records = cur.execute("select count(*) from population_data").fetchone()[0]
        regions, y1, y2 = cur.execute("select count(distinct region), min(year), max(year) from population_data").fetchone()
        users = cur.execute("select count(*) from users").fetchone()[0]
        sources = cur.execute("select count(*) from data_sources").fetchone()[0]
        indicators = cur.execute("select count(*) from population_indicators").fetchone()[0]
    return {"records": records, "regions": regions, "years": f"{y1}-{y2}", "users": users, "sources": sources, "indicators": indicators}


def build_slides() -> list[Slide]:
    stats = db_stats()
    slides: list[Slide] = []

    s = Slide("Population-Insight 人口趋势与分析管理系统", "课程设计答辩")
    slide_chrome(s, 1)
    s.add(Element("text", 0.72, 0.95, 8.15, 1.85, s.title, fill=BG, line=BG, color=INK, font_size=30, bold=True, shape="rect"))
    s.add(Element("text", 0.78, 2.72, 7.2, 0.5, "Python + Flask + SQLite + ECharts 的人口数据管理、预测、可视化与报告平台", fill=BG, line=BG, color=MUTED, font_size=15, shape="rect"))
    for i, item in enumerate([("310", "人口年度记录"), ("31", "地区档案"), ("10 年", "2015-2024"), ("14", "已完成功能")]):
        x = 0.78 + i * 2.25
        value_size = 17 if len(item[0]) > 4 else 20
        s.add(Element("rect", x, 3.55, 1.9, 1.05, fill=WHITE, line=LINE))
        s.add(Element("text", x + 0.05, 3.69, 1.8, 0.34, item[0], fill=WHITE, line=WHITE, color=GREEN_DARK, font_size=value_size, bold=True, align="center", shape="rect"))
        s.add(Element("text", x + 0.1, 4.15, 1.7, 0.25, item[1], fill=WHITE, line=WHITE, color=MUTED, font_size=10, align="center", shape="rect"))
    card(s, 9.1, 1.15, 3.25, 4.55, "项目定位", "围绕人口年度核心指标，形成数据采集、基础管理、查询筛选、统计排名、趋势预测、风险评估、报告生成与 CSV 导出的完整闭环。", fill="EEF6F2", accent=GREEN)
    slides.append(s)

    s = Slide("项目学习结论与技术栈", "项目概览")
    slide_chrome(s, 2)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    for x, title, body, accent in [
        (0.72, "后端", "Flask 路由层承接 Web 请求，服务层封装业务逻辑，SQLite 保存 8 张核心业务表。", GREEN),
        (4.65, "前端", "Jinja2 模板、CSS、JavaScript 与 ECharts 组成 Web 工作台，支持仪表盘、图表和交互筛选。", BLUE),
        (8.58, "分析", "统计分析、地区对比、线性回归、增长率拟合、结构变化识别与风险评分共同支撑决策。", GOLD),
    ]:
        card(s, x, 1.62, 3.45, 2.0, title, body, accent=accent)
    for i, (label, value) in enumerate([("人口记录", stats["records"]), ("地区", stats["regions"]), ("年份", stats["years"]), ("用户", stats["users"]), ("来源", stats["sources"]), ("扩展指标", stats["indicators"])]):
        x = 0.72 + (i % 3) * 3.93
        y = 4.25 + (i // 3) * 0.92
        s.add(Element("rect", x, y, 3.45, 0.66, fill="FDFEFE", line=LINE))
        s.add(Element("text", x + 0.16, y + 0.13, 1.25, 0.25, label, fill="FDFEFE", line="FDFEFE", color=MUTED, font_size=10, shape="rect"))
        s.add(Element("text", x + 1.35, y + 0.1, 1.8, 0.3, str(value), fill="FDFEFE", line="FDFEFE", color=GREEN_DARK, font_size=15, bold=True, align="right", shape="rect"))
    slides.append(s)

    s = Slide("现在已完成的 14 项功能", "功能完成情况")
    slide_chrome(s, 3)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    groups = [
        ("智能预测决策", "1. 机器学习人口趋势预测；2. 大模型结果解释分析；3. 智能风险评估", GREEN),
        ("可视化统计分析", "4. 数据可视化分析；5. 统计分析与地区排名；9. 多条件查询筛选；10. 数据排序与对比", BLUE),
        ("数据采集治理", "6. 人口数据采集；7. 人口数据管理；11. 地区档案管理；12. 数据来源管理", GOLD),
        ("系统支撑输出", "8. 分析报告生成；13. 扩展指标管理；14. CSV 数据导出；同时具备登录权限与操作日志", RED),
    ]
    for i, (title, body, accent) in enumerate(groups):
        card(s, 0.78 + (i % 2) * 6.05, 1.55 + (i // 2) * 2.25, 5.35, 1.72, title, body, fill=WHITE, accent=accent)
    pill(s, 4.6, 6.42, 4.0, "对应页面：/records /collection /statistics /comparison /prediction /charts /alerts /reports")
    slides.append(s)

    s = Slide("团队分工与模块边界", "团队分工")
    slide_chrome(s, 4)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    rows = [
        ("王景冉", "机器学习预测与智能决策分析模块", "趋势预测、时间序列建模、线性回归、增长率拟合、结构变化识别、老龄化风险评估、预测结果解释分析", GREEN),
        ("孙屿丰", "数据可视化与统计分析模块", "多条件筛选、数据排序、统计分析、地区排名、趋势图、柱状图、性别结构饼图、预测图表展示", BLUE),
        ("张金涛", "数据采集与基础数据管理模块", "人口数据爬取、公开统计数据采集、数据来源整理、人口数据增删改查、地区档案管理", GOLD),
        ("密政奇", "系统支撑与成果输出模块", "登录权限、扩展指标、年度指标录入、CSV 导出、日志、报告、预警、README、ER/DFD 和答辩材料", RED),
    ]
    for i, (name, module, body, accent) in enumerate(rows):
        y = 1.48 + i * 1.25
        s.add(Element("rect", 0.78, y, 11.75, 0.92, fill=WHITE, line=LINE))
        s.add(Element("rect", 0.78, y, 1.18, 0.92, fill=accent, line=accent))
        s.add(Element("text", 0.86, y + 0.22, 1.02, 0.3, name, fill=accent, line=accent, color=WHITE, font_size=13, bold=True, align="center", shape="rect"))
        s.add(Element("text", 2.12, y + 0.12, 2.65, 0.25, module, fill=WHITE, line=WHITE, color=INK, font_size=12, bold=True, shape="rect"))
        s.add(Element("text", 4.95, y + 0.12, 7.25, 0.56, body, fill=WHITE, line=WHITE, color=MUTED, font_size=9, shape="rect"))
    slides.append(s)

    s = Slide("系统总体架构", "系统架构")
    slide_chrome(s, 5)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    layers = [
        ("入口层", "Web 工作台 app.py；控制台 main.py", 0.95, GREEN),
        ("表示层", "Jinja2 模板、CSS、JavaScript、ECharts", 2.05, BLUE),
        ("服务层", "auth / population / collection / statistics / comparison / prediction / export / extension / log", 3.15, GOLD),
        ("数据层", "SQLite：users、population_data、regions、data_sources、indicators、reports、logs", 4.25, RED),
    ]
    for title, body, y, accent in layers:
        s.add(Element("rect", 1.05, y, 10.9, 0.78, fill=WHITE, line=LINE))
        s.add(Element("text", 1.25, y + 0.18, 1.25, 0.28, title, fill=WHITE, line=WHITE, color=accent, font_size=13, bold=True, shape="rect"))
        s.add(Element("text", 2.68, y + 0.18, 8.85, 0.28, body, fill=WHITE, line=WHITE, color=INK, font_size=12, shape="rect"))
        if y < 4.2:
            s.add(Element("arrow", 6.35, y + 0.8, 0.25, 0.42, fill=accent, line=accent, shape="downArrow"))
    card(s, 1.05, 5.35, 10.9, 1.05, "架构特点", "路由只处理请求与页面，服务层集中业务逻辑，数据库初始化脚本统一建表和种子数据，Web 与控制台复用同一套服务能力。", fill="EEF6F2")
    slides.append(s)

    s = Slide("自顶向下设计图", "概要设计")
    slide_chrome(s, 6)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    s.add(Element("rect", 4.55, 1.35, 4.2, 0.65, fill=GREEN, line=GREEN))
    s.add(Element("text", 4.72, 1.52, 3.86, 0.24, "Population-Insight 系统", fill=GREEN, line=GREEN, color=WHITE, font_size=14, bold=True, align="center", shape="rect"))
    top = [("数据采集治理", 1.0, GOLD), ("分析预测决策", 4.15, GREEN), ("可视化统计", 7.3, BLUE), ("支撑与输出", 10.45, RED)]
    for title, x, accent in top:
        s.add(Element("arrow", 6.45, 2.02, x - 6.1, 0.55, fill=accent, line=accent, shape="line"))
        s.add(Element("rect", x, 2.65, 2.1, 0.58, title, fill=accent, line=accent, color=WHITE, font_size=11, bold=True, align="center", valign="mid"))
    sub = [
        (0.62, ["公开数据采集", "人口数据 CRUD", "地区/来源维护"], GOLD_SOFT),
        (3.78, ["线性回归预测", "增长率拟合", "风险评估/解释"], MINT),
        (6.93, ["趋势图/柱状图", "饼图/预测图", "统计排名/对比"], BLUE_SOFT),
        (10.08, ["登录权限", "扩展指标", "报告/CSV/日志"], RED_SOFT),
    ]
    for x, items, fill in sub:
        for i, item in enumerate(items):
            s.add(Element("rect", x, 3.65 + i * 0.68, 2.85, 0.43, item, fill=fill, line=LINE, color=INK, font_size=9, align="center", valign="mid"))
    slides.append(s)

    s = Slide("ER 图：8 张核心表与关系", "数据库设计")
    slide_chrome(s, 7)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    tables = [
        ("users", "用户与角色", 0.75, 1.55, GREEN),
        ("operation_logs", "操作审计", 0.75, 3.0, GREEN),
        ("analysis_reports", "分析报告", 0.75, 4.45, GREEN),
        ("population_data", "年度人口核心数据", 4.55, 2.35, BLUE),
        ("regions", "地区档案", 8.8, 1.35, GOLD),
        ("data_sources", "数据来源", 8.8, 2.65, GOLD),
        ("population_indicators", "扩展指标定义", 8.8, 4.05, RED),
        ("annual_indicator_values", "年度扩展指标值", 8.8, 5.25, RED),
    ]
    for name, desc, x, y, accent in tables:
        s.add(Element("rect", x, y, 2.9, 0.78, fill=WHITE, line=accent))
        s.add(Element("text", x + 0.1, y + 0.1, 2.7, 0.22, name, fill=WHITE, line=WHITE, color=accent, font_size=11, bold=True, align="center", shape="rect"))
        s.add(Element("text", x + 0.1, y + 0.42, 2.7, 0.18, desc, fill=WHITE, line=WHITE, color=MUTED, font_size=8, align="center", shape="rect"))
    for x, y, w, h, c in [(3.62, 1.91, 0.9, 0.9, GREEN), (3.62, 4.82, 0.9, -1.62, GREEN), (7.45, 1.75, 1.28, 0.85, GOLD), (7.45, 3.03, 1.28, 0.0, GOLD), (7.45, 4.45, 1.28, 1.2, RED)]:
        s.add(Element("arrow", x, y, w, h, fill=c, line=c, shape="line"))
    pill(s, 4.2, 6.55, 4.8, "逻辑关联：username、region、indicator_code 与来源说明支撑业务追踪")
    slides.append(s)

    s = Slide("DFD 上下文图", "数据流设计")
    slide_chrome(s, 8)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    s.add(Element("rect", 4.6, 2.45, 4.1, 1.2, "Population-Insight 人口趋势与分析系统", fill=GREEN, line=GREEN, color=WHITE, font_size=14, bold=True, align="center", valign="mid"))
    nodes = [("管理员", 0.9, 1.55, GREEN), ("普通用户", 0.9, 4.7, BLUE), ("公开统计数据源", 9.9, 1.55, GOLD), ("大模型服务（可选）", 9.9, 4.7, RED), ("CSV / 报告 / 图表", 4.95, 5.65, GREEN_DARK)]
    for text, x, y, accent in nodes:
        s.add(Element("rect", x, y, 2.2, 0.62, text, fill=WHITE, line=accent, color=INK, font_size=11, bold=True, align="center", valign="mid"))
    for x, y, w, h, c in [(3.18, 1.86, 1.38, 0.85, GREEN), (3.18, 5.0, 1.38, -1.75, BLUE), (9.9, 1.86, -1.15, 0.92, GOLD), (9.9, 5.0, -1.15, -1.75, RED), (6.65, 3.7, 0, 1.85, GREEN_DARK)]:
        s.add(Element("arrow", x, y, w, h, fill=c, line=c, shape="line"))
    card(s, 0.85, 6.05, 11.6, 0.95, "外部交互", "管理员维护数据与来源，普通用户查询分析，公开数据源进入采集流程，预测解释可接入大模型，最终输出报告、图表和 CSV。", fill="EEF6F2")
    slides.append(s)

    s = Slide("DFD 0 层与关键业务流", "数据流设计")
    slide_chrome(s, 9)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    processes = [("P1 登录权限", 0.75, 1.6, GREEN), ("P2 数据采集管理", 3.15, 1.6, GOLD), ("P3 查询筛选对比", 5.72, 1.6, BLUE), ("P4 统计可视化", 8.25, 1.6, BLUE), ("P5 预测风险解释", 10.75, 1.6, RED)]
    for text, x, y, accent in processes:
        s.add(Element("rect", x, y, 1.85, 0.7, text, fill=WHITE, line=accent, color=accent, font_size=10, bold=True, align="center", valign="mid"))
    for i in range(4):
        s.add(Element("arrow", 2.58 + i * 2.52, 1.94, 0.5, 0, fill=LINE, line=LINE, shape="line"))
    stores = [("D1 users", 0.85, 3.35), ("D2 population_data", 3.15, 3.35), ("D3 regions / D4 sources", 5.55, 3.35), ("D5 indicators / D6 values", 8.0, 3.35), ("D7 reports / D8 logs", 10.45, 3.35)]
    for text, x, y in stores:
        s.add(Element("rect", x, y, 2.05, 0.55, text, fill="FDFEFE", line=LINE, color=INK, font_size=9, align="center", valign="mid"))
    card(s, 0.9, 4.65, 3.65, 1.35, "采集导入流程", "公开 URL 或表格文本 → HTML/CSV 解析 → 字段校验与单位换算 → 写入 population_data → 记录数据来源和操作日志", accent=GOLD)
    card(s, 4.9, 4.65, 3.65, 1.35, "预测解释流程", "选择地区/指标/预测年数 → 读取历史数据 → 线性回归与增长率融合 → 风险评分 → 本地规则或大模型解释 → 保存报告", accent=RED)
    card(s, 8.9, 4.65, 3.2, 1.35, "输出流程", "筛选结果、统计摘要、预测解释均可进入分析报告；列表数据支持 CSV 导出，关键操作进入日志审计。", accent=GREEN)
    slides.append(s)

    s = Slide("成果展示与答辩演示路线", "项目成果")
    slide_chrome(s, 10)
    s.add(Element("text", 0.65, 0.75, 8.0, 0.6, s.title, fill=BG, line=BG, color=INK, font_size=28, bold=True, shape="rect"))
    steps = [
        ("1", "登录进入仪表盘", "展示记录数、地区数、年份范围和最新日志"),
        ("2", "数据采集与管理", "演示粘贴表格、预览导入、筛选排序与增删改查"),
        ("3", "统计与可视化", "展示地区排名、趋势图、柱状图、性别结构图和地区对比"),
        ("4", "预测与风险评估", "演示融合预测、结构变化识别、风险等级和解释文本"),
        ("5", "报告与导出", "保存分析报告，导出 CSV，查看操作日志与扩展指标"),
    ]
    for i, (num, title, body) in enumerate(steps):
        y = 1.45 + i * 0.92
        s.add(Element("rect", 0.9, y, 0.5, 0.5, num, fill=GREEN if i < 3 else BLUE, line=GREEN if i < 3 else BLUE, color=WHITE, font_size=13, bold=True, align="center", valign="mid"))
        s.add(Element("text", 1.62, y - 0.02, 2.35, 0.24, title, fill=BG, line=BG, color=INK, font_size=13, bold=True, shape="rect"))
        s.add(Element("text", 4.1, y - 0.02, 7.7, 0.25, body, fill=BG, line=BG, color=MUTED, font_size=10, shape="rect"))
    s.add(Element("rect", 0.9, 6.35, 11.35, 0.55, "答辩主线：用真实人口数据完成采集、治理、分析、预测、解释和成果输出闭环。", fill=GREEN_DARK, line=GREEN_DARK, color=WHITE, font_size=13, bold=True, align="center", valign="mid"))
    slides.append(s)
    return slides


def render_preview(slide: Slide, idx: int) -> Path:
    image = Image.new("RGB", (PX_W, PX_H), rgb(BG))
    draw = ImageDraw.Draw(image)
    for e in slide.elements:
        box = px_rect(e)
        if e.kind == "arrow" and e.shape == "line":
            x1, y1 = int(e.x * SX), int(e.y * SY)
            x2, y2 = int((e.x + e.w) * SX), int((e.y + e.h) * SY)
            draw.line((x1, y1, x2, y2), fill=rgb(e.line), width=4)
            angle = math.atan2(y2 - y1, x2 - x1)
            ah = 16
            pts = [
                (x2, y2),
                (x2 - ah * math.cos(angle - 0.45), y2 - ah * math.sin(angle - 0.45)),
                (x2 - ah * math.cos(angle + 0.45), y2 - ah * math.sin(angle + 0.45)),
            ]
            draw.polygon(pts, fill=rgb(e.line))
            continue
        if e.kind in {"rect", "text", "arrow"}:
            if e.shape == "downArrow":
                x1, y1, x2, y2 = box
                mx = (x1 + x2) // 2
                pts = [(x1, y1), (x2, y1), (x2, y1 + (y2 - y1) * 2 // 3), (mx + 18, y1 + (y2 - y1) * 2 // 3), (mx, y2), (mx - 18, y1 + (y2 - y1) * 2 // 3), (x1, y1 + (y2 - y1) * 2 // 3)]
                draw.polygon(pts, fill=rgb(e.fill))
            else:
                if e.radius:
                    draw.rounded_rectangle(box, radius=10, fill=rgb(e.fill), outline=rgb(e.line), width=max(1, e.weight))
                else:
                    draw.rectangle(box, fill=rgb(e.fill), outline=rgb(e.line), width=max(1, e.weight))
            if e.text:
                draw_text(draw, box, e.text, e.font_size * 2, e.color, e.bold, e.align, e.valign)
    path = PREVIEW_DIR / f"slide{idx:02d}.png"
    image.save(path)
    return path


def text_body(e: Element) -> str:
    paragraphs = e.text.split("\n")
    ps = []
    for para in paragraphs:
        ps.append(
            f"""<a:p><a:r><a:rPr lang="zh-CN" sz="{e.font_size * 100}" b="{1 if e.bold else 0}"><a:solidFill><a:srgbClr val="{e.color}"/></a:solidFill><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>{esc(para)}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="{e.font_size * 100}"/></a:p>"""
        )
    anchor = "ctr" if e.valign == "mid" else "t"
    align = {"center": "ctr", "right": "r"}.get(e.align, "l")
    ps = [p.replace("<a:p>", f'<a:p><a:pPr algn="{align}"/>', 1) for p in ps]
    return f"""<p:txBody><a:bodyPr wrap="square" anchor="{anchor}" lIns="91440" tIns="45720" rIns="91440" bIns="45720"/><a:lstStyle/>{''.join(ps)}</p:txBody>"""


def shape_xml(e: Element, shape_id: int) -> str:
    preset = e.shape if e.shape not in {"line"} else "rect"
    no_fill = e.kind == "text" and e.fill == BG
    fill = "<a:noFill/>" if no_fill else f'<a:solidFill><a:srgbClr val="{e.fill}"/></a:solidFill>'
    line = f'<a:ln w="{max(1, e.weight) * 9525}"><a:solidFill><a:srgbClr val="{e.line}"/></a:solidFill></a:ln>'
    tx = text_body(e) if e.text else ""
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(e.x)}" y="{emu(e.y)}"/><a:ext cx="{emu(e.w)}" cy="{emu(e.h)}"/></a:xfrm>
        <a:prstGeom prst="{preset}"><a:avLst/></a:prstGeom>
        {fill}{line}
      </p:spPr>
      {tx}
    </p:sp>
    """


def connector_xml(e: Element, shape_id: int) -> str:
    x1 = e.x
    y1 = e.y
    x2 = e.x + e.w
    y2 = e.y + e.h
    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(e.w) or 0.01
    h = abs(e.h) or 0.01
    flip_h = ' flipH="1"' if e.w < 0 else ""
    flip_v = ' flipV="1"' if e.h < 0 else ""
    return f"""
    <p:cxnSp>
      <p:nvCxnSpPr><p:cNvPr id="{shape_id}" name="Connector {shape_id}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
      <p:spPr>
        <a:xfrm{flip_h}{flip_v}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom>
        <a:ln w="25400"><a:solidFill><a:srgbClr val="{e.line}"/></a:solidFill><a:tailEnd type="triangle"/></a:ln>
      </p:spPr>
    </p:cxnSp>
    """


def slide_xml(slide: Slide) -> str:
    items = []
    for i, e in enumerate(slide.elements, start=2):
        if e.kind == "arrow" and e.shape == "line":
            items.append(connector_xml(e, i))
        else:
            items.append(shape_xml(e, i))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    {''.join(items)}
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def package_pptx(slides: list[Slide]) -> None:
    with zipfile.ZipFile(PPTX_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        overrides = [
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '<Default Extension="xml" ContentType="application/xml"/>',
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
        ]
        for i in range(1, len(slides) + 1):
            overrides.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        z.writestr("[Content_Types].xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{''.join(overrides)}</Types>""")
        z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>""")
        slide_ids = "".join([f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in range(1, len(slides) + 1)])
        z.writestr("ppt/presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{len(slides)+1}"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="{emu(SLIDE_W)}" cy="{emu(SLIDE_H)}" type="screen4x3"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/></p:presentation>""")
        rels = [f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>' for i in range(1, len(slides) + 1)]
        rels.append(f'<Relationship Id="rId{len(slides)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>')
        rels.append(f'<Relationship Id="rId{len(slides)+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>')
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>""")
        z.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""")
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""")
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")
        z.writestr("ppt/theme/theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="PopulationInsight"><a:themeElements><a:clrScheme name="Custom"><a:dk1><a:srgbClr val="1E2A29"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F5E49"/></a:dk2><a:lt2><a:srgbClr val="F6F8F6"/></a:lt2><a:accent1><a:srgbClr val="2F7D62"/></a:accent1><a:accent2><a:srgbClr val="356C9B"/></a:accent2><a:accent3><a:srgbClr val="B7892B"/></a:accent3><a:accent4><a:srgbClr val="B45B5B"/></a:accent4><a:accent5><a:srgbClr val="5E6B68"/></a:accent5><a:accent6><a:srgbClr val="C7D4CF"/></a:accent6><a:hlink><a:srgbClr val="356C9B"/></a:hlink><a:folHlink><a:srgbClr val="2F7D62"/></a:folHlink></a:clrScheme><a:fontScheme name="Microsoft YaHei"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme><a:fmtScheme name="Clean"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle/></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>""")
        for i, slide in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(slide))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>""")
        z.writestr("docProps/core.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Population-Insight 答辩汇报</dc:title><dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy></cp:coreProperties>""")
        z.writestr("docProps/app.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Codex</Application><PresentationFormat>宽屏</PresentationFormat><Slides>{len(slides)}</Slides></Properties>""")


def make_contact_sheet(paths: Iterable[Path]) -> None:
    thumbs = []
    for path in paths:
        img = Image.open(path).resize((320, 180))
        thumbs.append(img)
    sheet = Image.new("RGB", (320 * 2, 180 * 5), rgb("FFFFFF"))
    for i, img in enumerate(thumbs):
        sheet.paste(img, ((i % 2) * 320, (i // 2) * 180))
    sheet.save(CONTACT_SHEET_PATH)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    slides = build_slides()
    previews = [render_preview(slide, i) for i, slide in enumerate(slides, start=1)]
    make_contact_sheet(previews)
    package_pptx(slides)
    print(f"PPTX: {PPTX_PATH}")
    print(f"Previews: {PREVIEW_DIR}")
    print(f"Contact sheet: {CONTACT_SHEET_PATH}")
    print(f"Slides: {len(slides)}")


if __name__ == "__main__":
    main()
