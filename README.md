# 人口趋势与分析管理系统

`Population-Insight` 是一个基于 `Python + Flask + SQLite + ECharts + Matplotlib` 的人口数据管理与分析系统，提供 Web 端工作台和控制台入口，适合课程设计、数据库实验、可视化分析演示和中小型数据平台原型展示。

![侧边栏预览](docs/images/sidebar-preview.png)

## 项目亮点

- 一套系统覆盖人口数据录入、查询、对比、预测、预警、报告与导出
- 内置登录、角色权限、操作日志和扩展指标管理
- 预置示例数据库，启动后即可直接演示
- 同时支持 Web 图表展示和后端图表导出
- 新增全国 1950-2025 年人口统计长序列，用于全国趋势观察与预测展示

## 技术栈

- 后端：Python、Flask
- 数据库：SQLite
- 前端：HTML、CSS、JavaScript
- 图表：ECharts、Matplotlib
- 架构：配置层 / 数据层 / 服务层 / Web 层 / 控制台 UI 层

## 主要功能

### 核心分析

- 概览仪表盘
- 统计分析
- 地区对比分析
- 人口趋势预测
- 全国长序列分析
- 图表中心
- 人口预警分析
- 分析报告管理

### 数据治理

- 人口数据管理、筛选、排序、分页
- 人口数据新增、编辑、删除
- 数据采集与导入
- 地区档案维护
- 数据来源维护
- 扩展指标与年度指标值维护

### 系统管理

- 用户登录与会话管理
- 管理员 / 普通用户角色权限区分
- 操作日志留痕

## 内置账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 普通用户 | `viewer` | `viewer123` |

## 快速开始

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

### 3. 启动控制台版本

```bash
python main.py
```

## 首次启动会自动完成

- 初始化 `data/population_insight.db`
- 创建业务数据表
- 插入默认用户
- 导入人口样例数据
- 导入全国人口 1950-2025 年长序列数据
- 导入地区、来源、扩展指标与演示数据

## Web 页面入口

| 路径 | 功能 |
| --- | --- |
| `/login` | 登录 |
| `/` | 概览仪表盘 |
| `/records` | 数据管理 |
| `/records/new` | 新增人口数据 |
| `/collection` | 数据采集与导入 |
| `/statistics` | 统计分析 |
| `/comparison` | 地区对比分析 |
| `/prediction` | 趋势预测 |
| `/national-series` | 全国长序列分析 |
| `/charts` | 图表中心 |
| `/export` | CSV 导出 |
| `/alerts` | 人口预警分析 |
| `/reports` | 分析报告 |
| `/regions` | 地区档案 |
| `/sources` | 数据来源 |
| `/indicators` | 扩展指标 |
| `/logs` | 操作日志 |

## 数据与分析能力

- 人口年度数据查询、组合筛选、排序与分页
- 全国 1950-2025 年总人口、出生率、死亡率、自然增长率、城镇化率长序列分析
- 地区维度指标对比与排名
- 基于历史数据的人口趋势预测
- 人口结构风险识别与预警提示
- 趋势图、柱状图、性别结构图等可视化图表
- CSV 导出与分析报告保存

## 全国长序列数据口径

- `national_population_series` 独立保存全国年度长序列，避免与省级 `population_data` 混用。
- 1950-1959 年数据按国家统计局《中国统计年鉴》早期人口长序列整理。
- 1960-2024 年使用 World Bank WDI 指标并交叉官方统计来源，覆盖总人口、出生率、死亡率、城镇人口和城镇化率。
- 2025 年使用国家统计局《中华人民共和国2025年国民经济和社会发展统计公报》：年末全国人口 140489 万人，出生率 5.63‰，死亡率 8.04‰，自然增长率 -2.41‰。

## 项目结构

```text
Population-Insight-main/
├─ app.py
├─ main.py
├─ requirements.txt
├─ README.md
├─ data/
├─ docs/
├─ output/
├─ population_insight/
│  ├─ config.py
│  ├─ db/
│  ├─ services/
│  ├─ ui/
│  ├─ utils/
│  └─ web/
├─ static/
│  ├─ css/
│  ├─ images/
│  └─ js/
└─ templates/
```

## 预警规则示例

系统当前内置的人口预警规则包括：

- 老龄化率 `>= 20%`
- 自然增长率 `< 0`
- 出生率 `< 7%`

## 相关文档

- [ER_DFD.md](docs/ER_DFD.md)：ER 图、DFD 与业务数据流设计
- [DEFENSE_MATERIALS.md](docs/DEFENSE_MATERIALS.md)：答辩材料与演示建议

## 适用场景

- 数据库课程设计
- Flask Web 项目练习
- 数据治理与分析平台原型
- 人口统计与可视化展示项目

## License

本项目使用 [LICENSE](LICENSE) 中声明的许可证。
