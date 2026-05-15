ADMIN_MENU_OPTIONS = {
    "1": "新增人口数据",
    "2": "基础查询",
    "3": "条件筛选",
    "4": "数据排序",
    "5": "修改数据",
    "6": "删除数据",
    "7": "统计分析",
    "8": "图形可视化",
    "9": "导出 CSV",
    "10": "查看操作日志",
    "11": "退出系统",
}

VIEWER_MENU_OPTIONS = {
    "1": "基础查询",
    "2": "条件筛选",
    "3": "数据排序",
    "4": "统计分析",
    "5": "图形可视化",
    "6": "导出 CSV",
    "7": "退出系统",
}


def print_banner() -> None:
    print("=" * 66)
    print("        人口趋势与分析管理系统")
    print("   Population Trend Analysis and Management System")
    print("=" * 66)


def print_login_tip() -> None:
    print("默认账号：admin/admin123  或  viewer/viewer123")


def print_menu(role: str) -> None:
    options = ADMIN_MENU_OPTIONS if role == "admin" else VIEWER_MENU_OPTIONS
    print("\n当前菜单：")
    for key, label in options.items():
        print(f"{key}. {label}")
