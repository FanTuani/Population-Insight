# Population Insight 人口趋势与分析管理系统

`Population Insight` 是一个基于 `Flask + SQLite + Jinja2 + ECharts` 的人口数据管理、分析与可视化系统。项目面向课程设计、数据库实验、数据可视化展示和答辩演示，提供从数据录入、治理、统计、对比、预测、预警到报告沉淀的一体化 Web 工作台。

系统保留轻量级 Flask 架构，不依赖 React/Vue 等大型前端框架，适合本地部署、课堂演示和二次开发。

![侧边栏预览](docs/images/sidebar-preview.png)

## 功能亮点

- 政务数据后台风格 UI：清爽、可信、信息密度高，支持折叠侧边栏和移动端导航。
- 内置权限与账号体系：管理员和普通用户分权访问。
- 支持人口数据新增、编辑、删除、筛选、排序、分页、CSV 导入与导出。
- 支持全国 1950-2025 年人口长序列分析。
- 支持 31 个省级地区 2015-2024 年年度人口数据演示。
- 支持中国地图热力展示，省份悬停高亮并显示人口指标。
- 支持统计分析、地区对比、趋势预测、图表中心、预警分析和分析报告。
- 指标旁提供 `?` 概念解释，说明出生率、死亡率、自然增长率、老龄化率、城镇化率等含义和计算方式。
- 系统管理包含日志、设置、用户和权限相关页面，适合答辩展示完整性。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | Python, Flask |
| 数据库 | SQLite |
| 模板 | Jinja2 |
| 前端 | HTML, CSS, JavaScript |
| 可视化 | ECharts, Matplotlib |
| 数据处理 | Python 标准库与服务层模块 |

## 默认账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 普通用户 | `viewer` | `viewer123` |

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Web 系统

```bash
python app.py
```

默认访问地址：

```text
http://127.0.0.1:5000
```

### 3. 可选：启动控制台版本

```bash
python main.py
```

## 自动化验收测试

项目内置一套验收与回归测试，可检查数据库初始化、登录权限、主要页面、核心 API、CRUD、CSV 导入导出、统计、对比、预测和预警，并生成 HTML 报告与关键页面截图。

安装测试依赖：

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m playwright install chromium
```

运行完整验收：

```bash
python scripts/run_acceptance_tests.py
```

报告输出位置：

```text
output/automated_tests/latest/index.html
```

测试默认使用临时 SQLite 数据库，不会写入 `data/population_insight.db`。

## 首次启动自动初始化

首次运行时系统会自动完成：

- 创建 `data/population_insight.db`
- 创建用户、人口数据、地区、来源、指标、日志、报告等业务表
- 初始化默认账号
- 导入 31 个省级地区 2015-2024 年演示数据
- 导入全国 1950-2025 年人口长序列数据
- 导入数据来源、扩展指标和演示记录

## 数据口径

### 全国长序列

全国年度长序列单独存放在 `national_population_series`，不与省级年度表混用。

覆盖年份：`1950-2025`，共 76 年。

主要字段：

- `year`
- `total_population`
- `birth_rate`
- `death_rate`
- `natural_growth_rate`
- `urban_population`
- `urbanization_rate`
- `source_name`
- `source_url`
- `data_quality`
- `remarks`

2025 年数据口径：

- 年末全国人口：`140489` 万人
- 出生率：`5.63‰`
- 死亡率：`8.04‰`
- 自然增长率：`-2.41‰`

### 省级年度数据

省级年度数据存放在 `population_data`。

覆盖范围：

- 31 个省级地区
- 2015-2024 年
- 共 310 条年度记录

省级数据用于省份级管理、统计、对比、图表、预警和局部预测展示；全国长序列用于宏观趋势、全国对比和 1950 起始的长期预测展示。

## 指标说明

系统页面中的指标名旁带有 `?`，鼠标悬停可查看解释。

常用口径：

- 总人口：某地区年末常住人口总量。
- 出生率：`年出生人口数 / 年平均人口数 × 1000‰`
- 死亡率：`年死亡人口数 / 年平均人口数 × 1000‰`
- 自然增长率：`出生率 - 死亡率`
- 老龄化率：`老年人口数 / 总人口 × 100%`
- 城镇化率：`城镇人口 / 总人口 × 100%`
- 相对变化：`(当年值 - 基期值) / 基期值 × 100%`

## 主要页面

| 路径 | 功能 |
| --- | --- |
| `/login` | 登录 |
| `/` | 概览仪表盘 |
| `/records` | 人口数据管理 |
| `/records/new` | 新增人口记录 |
| `/collection` | 数据采集与导入 |
| `/statistics` | 统计分析 |
| `/comparison` | 数据对比分析 |
| `/prediction` | 趋势预测 |
| `/national-series` | 全国长序列 |
| `/charts` | 图表中心 |
| `/alerts` | 预警分析 |
| `/reports` | 分析报告 |
| `/regions` | 地区档案 |
| `/sources` | 数据来源 |
| `/indicators` | 扩展指标 |
| `/logs` | 操作日志 |
| `/settings` | 系统设置 |
| `/users` | 用户管理 |
| `/permissions` | 权限管理 |

## 核心 API

| API | 说明 |
| --- | --- |
| `/api/dashboard/map` | 仪表盘中国地图数据 |
| `/api/national-series/trend` | 全国长序列趋势数据 |
| `/api/charts/trend` | 图表中心趋势折线图 |
| `/api/charts/bar` | 年度柱状图 |
| `/api/charts/gender` | 性别结构饼图 |
| `/api/comparison` | 地区对比图表数据 |
| `/api/prediction/chart` | 趋势预测图表数据 |

## CSV 导入与导出

- 导出：在 `/records` 人口数据管理页面点击“导出当前结果”，系统会按当前筛选条件导出 CSV 文件。
- 导入：在 `/collection` 数据采集页面上传本地 `.csv` 文件，先预览识别结果，再确认导入到 MySQL/SQLite。
- 示例文件：`samples/population_import_sample.csv`，可直接用于演示 CSV 上传导入。

## 预测说明

趋势预测支持两类模式：

- 全国模式：默认使用全国 `1950-2025` 长序列，总人口预测图从 1950 年开始展示。
- 省级模式：使用省级 `2015-2024` 年度表，适合展示地区短期趋势。

全国预测入口默认选择“全国”，便于答辩时直接展示 1950 起始的长周期趋势。

## 预警规则示例

系统当前内置的人口预警逻辑包括：

- 老龄化率达到较高水平
- 自然增长率为负
- 出生率偏低
- 预测期末人口规模下降

预警结果用于课程演示和风险识别展示，不作为正式政策判断依据。

## 项目结构

```text
Population-Insight-main/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── data/
│   └── population_insight.db
├── docs/
│   ├── ER_DFD.md
│   └── DEFENSE_MATERIALS.md
├── population_insight/
│   ├── config.py
│   ├── db/
│   ├── services/
│   ├── ui/
│   └── utils/
├── static/
│   ├── css/
│   ├── images/
│   └── js/
└── templates/
```

## 相关文档

- [ER_DFD.md](docs/ER_DFD.md)：ER 图、DFD 与业务数据流设计
- [DEFENSE_MATERIALS.md](docs/DEFENSE_MATERIALS.md)：答辩材料与演示建议

## 适用场景

- 数据库课程设计
- Flask Web 项目实践
- 人口统计与可视化展示
- 数据治理平台原型
- 课程答辩与项目演示

## MySQL 配置

项目默认仍使用 SQLite，本地演示无需额外配置。要切换到 MySQL，请先创建数据库：

```sql
CREATE DATABASE population_insight CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

安装依赖：

```bash
pip install -r requirements.txt
```

PowerShell 启动示例：

```powershell
$env:POPULATION_INSIGHT_DB_ENGINE="mysql"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="你的MySQL密码"
$env:MYSQL_DATABASE="population_insight"
python app.py
```

首次启动时系统会自动在 MySQL 中创建业务表，并导入默认账号和演示数据。

## License

本项目使用 [LICENSE](LICENSE) 中声明的许可证。
