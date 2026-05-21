# 人口趋势与分析管理系统

`Population-Insight` 是一个基于 `Python + Flask + SQLite + Matplotlib + ECharts` 的人口数据管理与分析系统。项目提供 Web 主入口和控制台备用入口，适合作为课程设计、数据库实践或小型数据分析系统展示。

系统当前包含 **8 张数据表** 和 **21 项主要功能**，覆盖人口数据维护、查询筛选、统计分析、图表展示、CSV 导出、扩展指标、分析报告和人口预警。

## 技术栈

- 后端：Python、Flask
- 数据库：SQLite
- Web 图表：ECharts
- 后端图表：Matplotlib
- 前端：HTML、CSS、JavaScript
- 架构：数据库层、服务层、Web 层、控制台 UI 分层

## 所有功能

1. 用户登录与会话管理：支持管理员和普通用户登录。
2. 权限控制：管理员可维护数据，普通用户主要查看、分析和导出。
3. 数据库自动初始化：首次运行自动创建数据库、数据表、默认账号和样例数据。
4. 人口数据新增：录入地区、年份、总人口、性别人口、出生率、死亡率等指标。
5. 人口数据查询：按地区、年份查询人口年度数据。
6. 多条件筛选：支持年份区间、人口区间、出生率区间、老龄化率区间等筛选。
7. 数据排序：支持按 ID、地区、年份、总人口、出生率、死亡率、自然增长率、老龄化率、城镇化率排序。
8. 人口数据修改：管理员可编辑已有年度人口记录。
9. 人口数据删除：管理员可删除指定人口记录。
10. 统计分析：计算记录数量、平均总人口、平均出生率、平均老龄化率、最高/最低人口记录、地区增长率。
11. 地区排名：按最新年份或指定年份生成总人口排名。
12. 图形可视化：支持趋势图、地区对比柱状图、性别结构饼图。
13. CSV 导出：导出当前筛选结果到 `output/exports/`。
14. 操作日志查看：管理员可查看新增、修改、删除、扩展维护等操作留痕。
15. 地区档案管理：维护地区名称、地区类型、行政区划代码、上级地区和备注。
16. 数据来源管理：维护来源名称、发布机构、链接、发布日期、可信等级和备注。
17. 扩展指标管理：维护少儿人口占比、劳动年龄人口占比、总抚养比等可扩展指标定义。
18. 年度扩展指标录入：为指定地区、年份、指标录入扩展指标值。
19. 分析报告保存与查看：保存统计分析结果或手动录入分析摘要。
20. 人口预警分析：自动识别老龄化率较高、自然增长率为负、出生率偏低的记录。
21. 控制台备用入口：通过 `python main.py` 使用菜单式交互完成核心功能。

## 角色权限

| 角色 | 默认账号 | 权限说明 |
| --- | --- | --- |
| 管理员 | `admin / admin123` | 可新增、修改、删除人口数据，维护地区、来源、指标、查看日志 |
| 普通用户 | `viewer / viewer123` | 可查询、筛选、排序、统计、图表、导出、查看报告和预警 |

## 数据表设计

### `users`

用户表，保存登录账号和角色信息。

- `id`：主键
- `username`：用户名，唯一
- `password_hash`：密码哈希
- `role`：角色，`admin` 或 `viewer`
- `created_at`：创建时间

### `population_data`

人口年度核心数据表。

- `id`：主键
- `region`：地区
- `year`：年份
- `total_population`：总人口
- `male_population`：男性人口
- `female_population`：女性人口
- `birth_rate`：出生率
- `death_rate`：死亡率
- `natural_growth_rate`：自然增长率
- `aging_rate`：老龄化率
- `urbanization_rate`：城镇化率
- `remarks`：备注
- `created_at` / `updated_at`：创建和更新时间

约束：同一地区同一年份不能重复；男性人口与女性人口之和必须等于总人口。

### `operation_logs`

操作日志表。

- `id`：主键
- `username`：操作用户
- `action`：操作类型
- `target_id`：目标记录 ID
- `details`：操作说明
- `action_time`：操作时间

### `regions`

地区档案表。

- `id`：主键
- `name`：地区名称，唯一
- `region_type`：地区类型
- `admin_code`：行政区划代码
- `parent_region`：上级地区
- `remarks`：备注
- `created_at`：创建时间

### `data_sources`

数据来源表。

- `id`：主键
- `name`：来源名称，唯一
- `publisher`：发布机构
- `source_url`：来源链接
- `published_date`：发布日期，格式为 `YYYY-MM-DD`
- `reliability_level`：可信等级，取值为 `高`、`中`、`低`
- `remarks`：备注
- `created_at`：创建时间

### `population_indicators`

扩展指标定义表。

- `id`：主键
- `code`：指标编码，唯一
- `name`：指标名称
- `unit`：单位
- `description`：指标说明
- `created_at`：创建时间

### `annual_indicator_values`

年度扩展指标值表。

- `id`：主键
- `region`：地区
- `year`：年份
- `indicator_code`：指标编码，关联 `population_indicators.code`
- `value`：指标值
- `remarks`：备注
- `created_at`：创建时间

约束：同一地区、年份、指标只能录入一条值。

### `analysis_reports`

分析报告表。

- `id`：主键
- `title`：报告标题
- `username`：保存用户
- `filter_summary`：筛选条件摘要
- `report_summary`：分析摘要
- `created_at`：创建时间

## 目录结构

```text
Population-Insight/
├── app.py                         # Flask Web 主入口
├── main.py                        # 控制台备用入口
├── requirements.txt               # Python 依赖
├── README.md
├── data/
│   └── population_insight.db      # SQLite 数据库，运行时自动初始化
├── output/
│   ├── charts/                    # Matplotlib 图表输出
│   └── exports/                   # CSV 导出输出
├── population_insight/
│   ├── config.py                  # 配置、默认用户、初始化样例数据
│   ├── db/
│   │   ├── connection.py          # 数据库连接
│   │   └── initializer.py         # 建表和种子数据
│   ├── services/
│   │   ├── auth_service.py        # 登录认证
│   │   ├── dashboard_service.py   # 仪表盘和 Web 图表数据
│   │   ├── export_service.py      # CSV 导出
│   │   ├── extension_service.py   # 地区、来源、指标、报告、预警
│   │   ├── log_service.py         # 操作日志
│   │   ├── population_service.py  # 人口数据 CRUD、查询、排序
│   │   ├── statistics_service.py  # 统计分析和排名
│   │   └── visualization_service.py # Matplotlib 图表
│   ├── ui/
│   │   ├── menu.py                # 控制台菜单
│   │   └── prompts.py             # 控制台输入提示
│   ├── utils/
│   │   ├── formatters.py          # 表格和统计结果格式化
│   │   ├── security.py            # 密码哈希
│   │   └── validators.py          # 数据校验
│   └── web/
│       └── auth.py                # Web 登录和权限装饰器
├── static/
│   ├── css/app.css
│   ├── js/charts.js
│   └── favicon.svg
└── templates/                     # Flask 页面模板
```

## 安装与运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动 Web 系统：

```bash
python app.py
```

默认访问地址：

```text
http://127.0.0.1:5000
```

启动控制台备用入口：

```bash
python main.py
```

程序启动时会自动：

- 创建 `data/population_insight.db`
- 创建 8 张数据表
- 插入默认管理员和普通用户
- 插入北京市、广东省的初始化人口数据
- 插入地区档案、数据来源、扩展指标和年度扩展指标样例数据

## Web 页面入口

| 路径 | 功能 |
| --- | --- |
| `/login` | 登录 |
| `/` | 概览仪表盘 |
| `/records` | 人口数据管理、查询、筛选、排序 |
| `/records/new` | 新增人口数据 |
| `/statistics` | 统计分析、保存分析报告 |
| `/charts` | 图表中心 |
| `/export` | CSV 导出 |
| `/alerts` | 人口预警分析 |
| `/reports` | 分析报告 |
| `/regions` | 地区档案管理 |
| `/sources` | 数据来源管理 |
| `/indicators` | 扩展指标与年度指标值管理 |
| `/logs` | 操作日志 |

## 图表能力

Web 图表由 ECharts 渲染：

- 趋势图：展示某地区某指标的年度变化
- 柱状图：展示某年份各地区指标对比
- 饼图：展示某地区某年份的男女性别结构

控制台和后端图表能力由 Matplotlib 支持，生成文件保存在：

```text
output/charts/
```

CSV 导出文件保存在：

```text
output/exports/
```

## 人口预警规则

当前系统内置 3 条预警规则：

- `老龄化率 >= 20%`：标记为高等级预警
- `自然增长率 < 0`：标记为高等级预警
- `出生率 < 7%`：标记为中等级预警

预警结果可在 Web 端 `/alerts` 页面查看，也可在控制台菜单中查看。

## 数据校验规则

- 年份必须在系统配置范围内。
- 总人口、男性人口、女性人口等数量不能为负数。
- 出生率、死亡率、老龄化率、城镇化率不能为负数。
- 男性人口 + 女性人口必须等于总人口。
- 同一地区同一年份的人口数据不能重复。
- 同一地区、年份、指标的扩展指标值不能重复。
- 数据来源可信等级只能是 `高`、`中`、`低`。
- 数据来源发布日期必须使用 `YYYY-MM-DD` 格式。

## 答辩演示建议

1. 使用 `admin / admin123` 登录系统。
2. 进入概览页，展示记录数量、地区数量、年份范围和最近操作。
3. 在数据管理页演示查询、筛选、排序。
4. 新增一条人口数据，再编辑和删除，展示操作日志。
5. 在统计分析页展示平均值、最大最小值、地区增长率和排名。
6. 保存当前统计结果为分析报告，并到分析报告页查看。
7. 进入图表中心展示趋势图、柱状图、性别结构图。
8. 导出当前筛选结果 CSV。
9. 在地区档案、数据来源、扩展指标页面展示 8 张表扩展设计。
10. 在预警分析页展示人口预警结果。

## 参考数据说明

当前初始化数据为手动整理后的公开人口统计数据：

- 北京市：`2015-2024`
- 广东省：`2020-2024`

老龄化率统一按 `60 岁及以上常住人口占比` 处理。

主要参考来源：

- [北京市人口统计（首都之窗）](https://www.beijing.gov.cn/renwen/bjgk/rk/rktj/)
- [北京市 2022 年国民经济和社会发展统计公报](https://www.beijing.gov.cn/gate/big5/www.beijing.gov.cn/gongkai/shuju/tjgb/202304/t20230414_3032832.html)
- [广东省统计局](https://stats.gd.gov.cn/)
- [北京市历史人口数据整理页](https://www.zgrkk.com/population-history/27.html)
- [广东省历史人口数据整理页](https://www.zgrkk.com/population-history/1.html)
