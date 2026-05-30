from __future__ import annotations


def input_with_default(prompt_text: str, default: str | int | float | None = None) -> str:
    if default in (None, ""):
        return input(f"{prompt_text}：").strip()
    return input(f"{prompt_text}（当前 {default}，直接回车保留）：").strip()


def prompt_login_credentials() -> tuple[str, str]:
    username = input("用户名：").strip()
    password = input("密码：").strip()
    return username, password


def prompt_population_data(existing: dict | None = None) -> dict:
    existing = existing or {}
    return {
        "region": input_with_default("地区", existing.get("region")),
        "year": input_with_default("年份", existing.get("year")),
        "total_population": input_with_default("总人口", existing.get("total_population")),
        "male_population": input_with_default("男性人口", existing.get("male_population")),
        "female_population": input_with_default("女性人口", existing.get("female_population")),
        "birth_rate": input_with_default("出生率", existing.get("birth_rate")),
        "death_rate": input_with_default("死亡率", existing.get("death_rate")),
        "aging_rate": input_with_default("老龄化率", existing.get("aging_rate")),
        "urbanization_rate": input_with_default("城镇化率", existing.get("urbanization_rate")),
        "remarks": input_with_default("备注", existing.get("remarks", "")),
    }


def prompt_query_filters() -> dict:
    return {
        "region": input("地区关键字（可空）：").strip(),
        "year": input("年份（可空）：").strip(),
        "start_year": input("起始年份（可空）：").strip(),
        "end_year": input("结束年份（可空）：").strip(),
    }


def prompt_filter_conditions() -> dict:
    return {
        "region": input("地区关键字（可空）：").strip(),
        "start_year": input("起始年份（可空）：").strip(),
        "end_year": input("结束年份（可空）：").strip(),
        "min_total_population": input("总人口最小值（可空）：").strip(),
        "max_total_population": input("总人口最大值（可空）：").strip(),
        "min_birth_rate": input("出生率最小值（可空）：").strip(),
        "max_birth_rate": input("出生率最大值（可空）：").strip(),
        "min_aging_rate": input("老龄化率最小值（可空）：").strip(),
        "max_aging_rate": input("老龄化率最大值（可空）：").strip(),
    }


def prompt_sort_options() -> tuple[str, str]:
    print("可排序字段：id, region, year, total_population, birth_rate, death_rate, natural_growth_rate, aging_rate, urbanization_rate")
    field = input("请输入排序字段：").strip()
    order = input("请输入排序方式（asc/desc）：").strip() or "asc"
    return field, order


def prompt_statistics_filters() -> tuple[str, str, str]:
    region = input("统计地区（可空表示全部）：").strip()
    start_year = input("统计起始年份（可空）：").strip()
    end_year = input("统计结束年份（可空）：").strip()
    return region, start_year, end_year


def prompt_visualization_choice() -> str:
    print("1. 折线趋势图")
    print("2. 柱状对比图")
    print("3. 饼图（男女结构）")
    return input("请选择图表类型：").strip()


def prompt_export_path() -> str:
    return input("导出文件名或路径（直接回车用默认文件名）：").strip()


def pause() -> None:
    input("\n按回车键继续...")
