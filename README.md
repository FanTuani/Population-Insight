# 人口趋势与分析管理系统

一个基于 `Python + SQLite + Flask + Matplotlib + ECharts` 的课程设计项目，提供本地 Web 主入口和控制台备用入口，实现人口统计数据的持久化管理、分析、导出和可视化。

## 项目特点

- SQLite 数据库存储，支持数据持久化
- Flask Web 主入口，浏览器即可完成核心业务操作
- 控制台菜单备用入口，保留课程设计原始交互方案
- 模块化分层设计，数据库层、服务层、UI 层分离
- 自动初始化数据库和首批真实人口数据
- 内置管理员 / 普通用户权限控制
- 支持人口数据新增、查询、修改、删除
- 支持条件筛选、数据排序、统计分析
- 支持导出 CSV
- 支持 ECharts 网页交互图表与 Matplotlib 后端图表能力
- 支持操作日志记录
- 扩展为 8 张数据表，覆盖地区档案、数据来源、扩展指标、年度指标值和分析报告
- 支持人口预警分析，自动识别老龄化率高、自然增长率为负、出生率偏低等情况

## 功能模块

1. 用户登录与权限验证
2. 初始数据导入
3. 新增人口数据
4. 基础查询
5. 条件筛选
6. 数据排序
7. 修改数据
8. 删除数据
9. 统计分析
10. 图形可视化
11. CSV 导出
12. 操作日志查看
13. 地区档案管理
14. 数据来源管理
15. 扩展指标管理
16. 年度扩展指标录入
17. 分析报告保存与查看
18. 人口预警分析

## 目录结构

```text
Population-Insight/
├── app.py
├── main.py
├── static/
│   ├── css/
│   └── js/
├── templates/
├── requirements.txt
├── README.md
├── data/
├── output/
│   ├── charts/
│   └── exports/
└── population_insight/
    ├── config.py
    ├── db/
    │   ├── connection.py
    │   └── initializer.py
    ├── services/
    │   ├── auth_service.py
    │   ├── dashboard_service.py
    │   ├── export_service.py
    │   ├── log_service.py
    │   ├── population_service.py
    │   ├── statistics_service.py
    │   └── visualization_service.py
    ├── ui/
    │   ├── menu.py
    │   └── prompts.py
    └── web/
        └── auth.py
    ├── utils/
        ├── formatters.py
        ├── security.py
        └── validators.py
```

## 数据表设计

### `users`

- `id`：主键
- `username`：用户名
- `password_hash`：密码哈希值
- `role`：角色（`admin` / `viewer`）
- `created_at`：创建时间

### `population_data`

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
- `created_at` / `updated_at`：时间戳

### `operation_logs`

- `id`：主键
- `username`：操作用户
- `action`：操作类型
- `target_id`：目标记录 ID
- `details`：操作说明
- `action_time`：操作时间

### `regions`

- `id`：主键
- `name`：地区名称，唯一
- `region_type`：地区类型（省、直辖市、城市等）
- `admin_code`：行政区划代码
- `parent_region`：上级地区
- `remarks`：备注
- `created_at`：创建时间

### `data_sources`

- `id`：主键
- `name`：来源名称，唯一
- `publisher`：发布机构
- `source_url`：来源链接
- `published_date`：发布日期
- `reliability_level`：可信等级
- `remarks`：备注
- `created_at`：创建时间

### `population_indicators`

- `id`：主键
- `code`：指标编码，唯一
- `name`：指标名称
- `unit`：单位
- `description`：指标说明
- `created_at`：创建时间

### `annual_indicator_values`

- `id`：主键
- `region`：地区
- `year`：年份
- `indicator_code`：指标编码，关联 `population_indicators.code`
- `value`：指标值
- `remarks`：备注
- `created_at`：创建时间

### `analysis_reports`

- `id`：主键
- `title`：报告标题
- `username`：保存用户
- `filter_summary`：筛选条件摘要
- `report_summary`：分析摘要
- `created_at`：创建时间

## 默认账号

- 管理员：`admin / admin123`
- 普通用户：`viewer / viewer123`

## 安装与运行

```bash
pip install -r requirements.txt
python app.py
```

控制台备用入口：

```bash
python main.py
```

程序首次运行会自动：

- 创建 `data/population_insight.db`
- 创建数据表
- 插入默认用户
- 插入已整理的真实人口数据

## 图表输出

- Web 页面图表由 ECharts 直接渲染
- 折线图、柱状图、饼图的 Matplotlib 版本仍可保存到 `output/charts/`
- CSV 会导出到 `output/exports/`

## 适合答辩演示的流程

1. 运行 `python app.py`，使用管理员账号登录
2. 进入概览页展示数据规模与最近操作
3. 在数据管理页完成查询、筛选、排序
4. 新增一条某地区某年份的人口数据并回表验证
5. 进入统计分析页展示平均值、最大最小值和排名
6. 进入图表中心展示趋势图、柱状图、性别结构图
7. 导出当前筛选结果 CSV
8. 在地区档案、数据来源、扩展指标页面展示扩展后的数据表
9. 在统计分析页保存一份分析报告，并到分析报告页查看
10. 在预警分析页展示老龄化率、自然增长率、出生率预警
11. 在日志页展示操作留痕

## 说明

- 为保证数据一致性，系统要求：`男性人口 + 女性人口 = 总人口`
- 同一地区同一年份的数据不能重复录入
- 系统会自动计算并保存 `自然增长率 = 出生率 - 死亡率`
- 扩展指标采用 `population_indicators` + `annual_indicator_values` 的通用结构，后续可继续添加新指标而不修改主表结构
- 人口预警规则当前为：`老龄化率 >= 20%`、`自然增长率 < 0`、`出生率 < 7%`
- 当前内置初始化数据为手动整理后的真实数据：
  - 北京市：`2015-2024`
  - 广东省：`2020-2024`
- 当前导入数据中的 `老龄化率` 统一按 `60岁及以上常住人口占比` 处理
- 主要参考来源：
  - [北京市人口统计（首都之窗）](https://www.beijing.gov.cn/renwen/bjgk/rk/rktj/)
  - [北京市2022年国民经济和社会发展统计公报](https://www.beijing.gov.cn/gate/big5/www.beijing.gov.cn/gongkai/shuju/tjgb/202304/t20230414_3032832.html)
  - [2022年广东省国民经济和社会发展统计公报 PDF](https://stats.gd.gov.cn/attachment/0/517/517175/4146083.pdf)
  - [2024年广东省国民经济和社会发展统计公报 PDF](https://stats.gd.gov.cn/attachment/0/576/576336/4686764.pdf)
  - [北京市历史人口数据整理页](https://www.zgrkk.com/population-history/27.html)
  - [广东省历史人口数据整理页](https://www.zgrkk.com/population-history/1.html)
