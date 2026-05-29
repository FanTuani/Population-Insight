from __future__ import annotations

from population_insight.db.initializer import init_database
from population_insight.services.auth_service import login
from population_insight.services.collection_service import collect_population_records, import_collected_records
from population_insight.services.comparison_service import build_region_comparison
from population_insight.services.export_service import export_to_csv
from population_insight.services.extension_service import (
    add_analysis_report,
    add_annual_indicator_value,
    add_data_source,
    add_population_indicator,
    add_region,
    get_population_alerts,
    list_analysis_reports,
    list_annual_indicator_values,
    list_data_sources,
    list_population_indicators,
    list_regions,
)
from population_insight.services.log_service import list_operation_logs
from population_insight.services.population_service import (
    add_population_record,
    delete_population_record,
    get_population_record_by_id,
    query_population_records,
    sort_population_records,
    update_population_record,
)
from population_insight.services.prediction_service import build_population_prediction
from population_insight.services.statistics_service import (
    calculate_statistics,
    get_region_ranking,
)
from population_insight.services.visualization_service import (
    draw_bar_chart,
    draw_gender_pie_chart,
    draw_trend_chart,
)
from population_insight.ui.menu import print_banner, print_login_tip, print_menu
from population_insight.ui.prompts import (
    pause,
    prompt_export_path,
    prompt_filter_conditions,
    prompt_login_credentials,
    prompt_population_data,
    prompt_query_filters,
    prompt_sort_options,
    prompt_statistics_filters,
    prompt_visualization_choice,
)
from population_insight.utils.formatters import records_to_table, statistics_to_lines
from population_insight.utils.validators import ensure_non_negative_number, ensure_year


def clean_filters(raw_filters: dict) -> dict:
    return {key: value for key, value in raw_filters.items() if value not in ("", None)}


def show_records(records: list[dict], title: str = "查询结果") -> None:
    print(f"\n{title}")
    print(records_to_table(records))
    print(f"\n共 {len(records)} 条记录。")


def handle_add(username: str) -> None:
    data = prompt_population_data()
    record_id = add_population_record(data, username=username)
    print(f"新增成功，记录 ID：{record_id}")


def handle_query() -> list[dict]:
    records = query_population_records(clean_filters(prompt_query_filters()))
    show_records(records, "基础查询结果")
    return records


def handle_filter() -> list[dict]:
    records = query_population_records(clean_filters(prompt_filter_conditions()))
    show_records(records, "条件筛选结果")
    return records


def handle_sort(last_records: list[dict]) -> list[dict]:
    if not last_records:
        print("当前没有缓存结果，将自动读取全部数据后排序。")
        last_records = query_population_records()

    field, order = prompt_sort_options()
    records = sort_population_records(last_records, field, order)
    show_records(records, "排序结果")
    return records


def handle_update(username: str) -> None:
    record_id = int(ensure_non_negative_number(input("请输入要修改的记录 ID：").strip(), "记录ID", integer=True))
    existing = get_population_record_by_id(record_id)
    if not existing:
        raise ValueError("未找到该记录。")

    print("当前记录：")
    print(records_to_table([existing]))
    updates = prompt_population_data(existing)
    update_population_record(record_id, updates, username=username)
    print("修改成功。")


def handle_delete(username: str) -> None:
    record_id = int(ensure_non_negative_number(input("请输入要删除的记录 ID：").strip(), "记录ID", integer=True))
    existing = get_population_record_by_id(record_id)
    if not existing:
        raise ValueError("未找到该记录。")

    print(records_to_table([existing]))
    confirm = input("确认删除请输入 y：").strip().lower()
    if confirm == "y":
        delete_population_record(record_id, username=username)
        print("删除成功。")
    else:
        print("已取消删除。")


def handle_statistics() -> None:
    region, start_year, end_year = prompt_statistics_filters()
    statistics = calculate_statistics(
        region=region or None,
        start_year=ensure_year(start_year) if start_year else None,
        end_year=ensure_year(end_year) if end_year else None,
    )
    print("\n统计分析结果")
    print(statistics_to_lines(statistics))

    ranking_year = end_year or start_year or ""
    try:
        ranking = get_region_ranking(
            metric="total_population",
            year=ensure_year(ranking_year) if ranking_year else None,
            top_n=5,
        )
    except ValueError:
        ranking = []
    print("\n总人口排名（前 5）")
    print(records_to_table(ranking, fields=[
        ("rank", "排名"),
        ("region", "地区"),
        ("year", "年份"),
        ("value", "指标值"),
    ]))


def handle_visualization() -> None:
    chart_type = prompt_visualization_choice()
    if chart_type == "1":
        region = input("请输入地区：").strip()
        metric = input("请输入指标（如 total_population/birth_rate）：").strip()
        path = draw_trend_chart(region, metric)
    elif chart_type == "2":
        year = ensure_year(input("请输入年份：").strip())
        metric = input("请输入指标（如 total_population/aging_rate）：").strip()
        path = draw_bar_chart(year, metric)
    elif chart_type == "3":
        region = input("请输入地区：").strip()
        year = ensure_year(input("请输入年份：").strip())
        path = draw_gender_pie_chart(region, year)
    else:
        raise ValueError("无效的图表类型。")

    print(f"图表已生成：{path}")


def handle_comparison() -> None:
    print("\n数据对比分析")
    regions_text = input("对比地区（多个地区用英文逗号分隔，留空默认前 5 个地区）：").strip()
    regions = [item.strip() for item in regions_text.split(",") if item.strip()]
    metric = input("对比指标（默认 total_population）：").strip() or "total_population"
    start_year_text = input("起始年份（可空）：").strip()
    end_year_text = input("结束年份（可空）：").strip()
    comparison = build_region_comparison(
        regions=regions,
        metric=metric,
        start_year=ensure_year(start_year_text) if start_year_text else None,
        end_year=ensure_year(end_year_text) if end_year_text else None,
    )

    print(f"\n{comparison['title']}")
    print(records_to_table(comparison["latest_rank"], fields=[
        ("rank", "排名"),
        ("region", "地区"),
        ("latest_value", "最新值"),
        ("change_percent", "区间变化%"),
        ("end_year", "年份"),
    ]))

    table_rows = []
    for row in comparison["table_rows"]:
        flat_row = {"year": row["year"]}
        flat_row.update(row["values"])
        table_rows.append(flat_row)
    fields = [("year", "年份")] + [(region, region) for region in comparison["regions"]]
    print("\n年度对比表")
    print(records_to_table(table_rows, fields=fields))


def handle_export(last_records: list[dict]) -> None:
    if not last_records:
        print("当前没有缓存结果，将导出全部数据。")
        last_records = query_population_records()

    output_path = prompt_export_path()
    path = export_to_csv(last_records, output_path or None)
    print(f"导出成功：{path}")


def handle_logs() -> None:
    logs = list_operation_logs()
    print(
        records_to_table(
            logs,
            fields=[
                ("id", "ID"),
                ("username", "用户名"),
                ("action", "操作"),
                ("target_id", "目标ID"),
                ("details", "详情"),
                ("action_time", "时间"),
            ],
        )
    )


def handle_regions(username: str) -> None:
    print(records_to_table(list_regions(), fields=[
        ("id", "ID"),
        ("name", "地区名称"),
        ("region_type", "类型"),
        ("admin_code", "行政代码"),
        ("parent_region", "上级地区"),
    ]))
    if input("是否新增地区档案？(y/N)：").strip().lower() == "y":
        record_id = add_region(
            {
                "name": input("地区名称：").strip(),
                "region_type": input("地区类型：").strip(),
                "admin_code": input("行政区划代码（可空）：").strip(),
                "parent_region": input("上级地区（可空）：").strip(),
                "remarks": input("备注（可空）：").strip(),
            },
            username=username,
        )
        print(f"地区档案已新增，ID：{record_id}")


def handle_data_sources(username: str) -> None:
    print(records_to_table(list_data_sources(), fields=[
        ("id", "ID"),
        ("name", "来源名称"),
        ("publisher", "发布机构"),
        ("published_date", "发布日期"),
        ("reliability_level", "可信等级"),
    ]))
    if input("是否新增数据来源？(y/N)：").strip().lower() == "y":
        record_id = add_data_source(
            {
                "name": input("来源名称：").strip(),
                "publisher": input("发布机构：").strip(),
                "source_url": input("来源链接（可空）：").strip(),
                "published_date": input("发布日期 YYYY-MM-DD（可空）：").strip(),
                "reliability_level": input("可信等级（高/中/低，默认中）：").strip() or "中",
                "remarks": input("备注（可空）：").strip(),
            },
            username=username,
        )
        print(f"数据来源已新增，ID：{record_id}")


def handle_indicators(username: str) -> None:
    print("\n指标定义")
    print(records_to_table(list_population_indicators(), fields=[
        ("id", "ID"),
        ("code", "编码"),
        ("name", "名称"),
        ("unit", "单位"),
        ("description", "说明"),
    ]))
    print("\n年度扩展指标值")
    print(records_to_table(list_annual_indicator_values(), fields=[
        ("id", "ID"),
        ("region", "地区"),
        ("year", "年份"),
        ("indicator_name", "指标"),
        ("value", "数值"),
    ]))
    choice = input("新增 1.指标定义 2.年度指标值 其他.返回：").strip()
    if choice == "1":
        record_id = add_population_indicator(
            {
                "code": input("指标编码：").strip(),
                "name": input("指标名称：").strip(),
                "unit": input("单位：").strip(),
                "description": input("说明（可空）：").strip(),
            },
            username=username,
        )
        print(f"指标定义已新增，ID：{record_id}")
    elif choice == "2":
        record_id = add_annual_indicator_value(
            {
                "region": input("地区：").strip(),
                "year": input("年份：").strip(),
                "indicator_code": input("指标编码：").strip(),
                "value": input("指标值：").strip(),
                "remarks": input("备注（可空）：").strip(),
            },
            username=username,
        )
        print(f"年度指标值已新增，ID：{record_id}")


def handle_reports(username: str, allow_create: bool = True) -> None:
    print(records_to_table(list_analysis_reports(), fields=[
        ("id", "ID"),
        ("title", "标题"),
        ("username", "用户"),
        ("filter_summary", "筛选条件"),
        ("created_at", "创建时间"),
    ]))
    if allow_create and input("是否新增分析报告？(y/N)：").strip().lower() == "y":
        record_id = add_analysis_report(
            {
                "title": input("报告标题：").strip(),
                "filter_summary": input("筛选条件摘要（可空）：").strip(),
                "report_summary": input("分析摘要：").strip(),
            },
            username=username,
        )
        print(f"分析报告已新增，ID：{record_id}")


def handle_alerts() -> None:
    alerts = get_population_alerts()
    print(records_to_table(alerts, fields=[
        ("region", "地区"),
        ("year", "年份"),
        ("alert_type", "预警类型"),
        ("severity", "等级"),
        ("message", "说明"),
    ]))
    print(f"\n共 {len(alerts)} 条预警。")


def handle_prediction() -> None:
    print("\n机器学习人口趋势预测")
    region = input("预测地区：").strip()
    metric = input("预测指标（默认 total_population）：").strip() or "total_population"
    forecast_years_text = input("预测年数（1-10，默认 5）：").strip() or "5"
    prediction = build_population_prediction(region, metric, int(forecast_years_text))

    print("\n模型摘要")
    print(f"模型：{prediction['model']['name']}")
    print(f"R2：{prediction['model']['r2']:.3f}")
    print(f"复合增长率：{prediction['model']['compound_growth_rate'] * 100:.2f}%")
    print(f"风险等级：{prediction['risk']['level']}，得分：{prediction['risk']['score']}")

    print("\n预测结果")
    print(records_to_table(prediction["predictions"], fields=[
        ("year", "年份"),
        ("linear_value", "线性回归"),
        ("growth_fit_value", "增长率拟合"),
        ("recent_trend_value", "近期趋势"),
        ("predicted_value", "融合预测"),
    ]))
    print("\n大模型解释分析")
    print(prediction["explanation"]["text"])


def handle_collection(username: str) -> None:
    print("\n人口数据采集")
    source_url = input("公开数据 URL（可空，留空则粘贴表格文本）：").strip()
    raw_text = ""
    if not source_url:
        print("请粘贴 CSV/制表符/HTML 表格文本，输入空行结束：")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        raw_text = "\n".join(lines)

    result = collect_population_records(raw_text=raw_text, source_url=source_url)
    records = result["records"]
    print(f"\n已识别 {len(records)} 条人口记录，预览前 10 条：")
    print(records_to_table(records[:10]))
    confirm = input("确认导入这些人口数据？(y/N)：").strip().lower()
    if confirm != "y":
        print("已取消导入。")
        return

    summary = import_collected_records(records, username=username)
    print(f"导入完成：成功 {summary['imported']} 条，失败 {summary['failed']} 条。")
    for error in summary["errors"][:10]:
        print(error)


def admin_loop(user: dict) -> None:
    last_records: list[dict] = []
    while True:
        print_menu(user["role"])
        choice = input("请选择功能：").strip()
        try:
            if choice == "1":
                handle_add(user["username"])
            elif choice == "2":
                last_records = handle_query()
            elif choice == "3":
                last_records = handle_filter()
            elif choice == "4":
                last_records = handle_sort(last_records)
            elif choice == "5":
                handle_update(user["username"])
            elif choice == "6":
                handle_delete(user["username"])
            elif choice == "7":
                handle_statistics()
            elif choice == "8":
                handle_visualization()
            elif choice == "9":
                handle_comparison()
            elif choice == "10":
                handle_export(last_records)
            elif choice == "11":
                handle_logs()
            elif choice == "12":
                handle_regions(user["username"])
            elif choice == "13":
                handle_data_sources(user["username"])
            elif choice == "14":
                handle_indicators(user["username"])
            elif choice == "15":
                handle_reports(user["username"])
            elif choice == "16":
                handle_alerts()
            elif choice == "17":
                handle_prediction()
            elif choice == "18":
                handle_collection(user["username"])
            elif choice == "19":
                print("系统已退出。")
                break
            else:
                print("请输入有效菜单编号。")
        except ValueError as error:
            print(f"操作失败：{error}")
        pause()


def viewer_loop(user: dict) -> None:
    last_records: list[dict] = []
    while True:
        print_menu(user["role"])
        choice = input("请选择功能：").strip()
        try:
            if choice == "1":
                last_records = handle_query()
            elif choice == "2":
                last_records = handle_filter()
            elif choice == "3":
                last_records = handle_sort(last_records)
            elif choice == "4":
                handle_statistics()
            elif choice == "5":
                handle_visualization()
            elif choice == "6":
                handle_comparison()
            elif choice == "7":
                handle_export(last_records)
            elif choice == "8":
                handle_reports(user["username"], allow_create=False)
            elif choice == "9":
                handle_alerts()
            elif choice == "10":
                handle_prediction()
            elif choice == "11":
                print("系统已退出。")
                break
            else:
                print("请输入有效菜单编号。")
        except ValueError as error:
            print(f"操作失败：{error}")
        pause()


def run() -> None:
    init_database()
    print_banner()
    print_login_tip()

    user = None
    while user is None:
        username, password = prompt_login_credentials()
        user = login(username, password)
        if user is None:
            print("登录失败，请重新输入。")

    print(f"\n欢迎你，{user['username']}（{user['role']}）")
    if user["role"] == "admin":
        admin_loop(user)
    else:
        viewer_loop(user)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n程序已中断。")
