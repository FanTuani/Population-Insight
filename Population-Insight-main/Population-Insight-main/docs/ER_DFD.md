# Population-Insight ER 图与 DFD 图

本文档用于课程设计、数据库实践和答辩材料展示，描述系统 8 张核心数据表之间的关系，以及人口趋势分析系统的数据流。

## ER 图

```mermaid
erDiagram
    users {
        INTEGER id PK
        TEXT username UK
        TEXT password_hash
        TEXT role
        TEXT created_at
    }

    population_data {
        INTEGER id PK
        TEXT region
        INTEGER year
        INTEGER total_population
        INTEGER male_population
        INTEGER female_population
        REAL birth_rate
        REAL death_rate
        REAL natural_growth_rate
        REAL aging_rate
        REAL urbanization_rate
        TEXT aging_rate_basis
        TEXT data_source_name
        TEXT source_url
        TEXT data_quality
        TEXT remarks
        TEXT created_at
        TEXT updated_at
    }

    operation_logs {
        INTEGER id PK
        TEXT username
        TEXT action
        INTEGER target_id
        TEXT details
        TEXT action_time
    }

    regions {
        INTEGER id PK
        TEXT name UK
        TEXT region_type
        TEXT admin_code
        TEXT parent_region
        TEXT remarks
        TEXT created_at
    }

    data_sources {
        INTEGER id PK
        TEXT name UK
        TEXT publisher
        TEXT source_url
        TEXT published_date
        TEXT reliability_level
        TEXT remarks
        TEXT created_at
    }

    population_indicators {
        INTEGER id PK
        TEXT code UK
        TEXT name
        TEXT unit
        TEXT description
        TEXT created_at
    }

    annual_indicator_values {
        INTEGER id PK
        TEXT region
        INTEGER year
        TEXT indicator_code FK
        REAL value
        TEXT remarks
        TEXT created_at
    }

    analysis_reports {
        INTEGER id PK
        TEXT title
        TEXT username
        TEXT filter_summary
        TEXT report_summary
        TEXT created_at
    }

    users ||--o{ operation_logs : "username records actions"
    users ||--o{ analysis_reports : "username saves reports"
    regions ||--o{ population_data : "name matches region"
    regions ||--o{ annual_indicator_values : "name matches region"
    population_indicators ||--o{ annual_indicator_values : "code maps indicator_code"
    population_data ||--o{ analysis_reports : "filtered statistics become reports"
    data_sources ||--o{ population_data : "source documents support data"
```

## DFD 上下文图

```mermaid
flowchart LR
    admin["管理员"]
    viewer["普通用户"]
    public_source["公开统计数据源"]
    llm["大模型服务(可选)"]
    system["Population-Insight 人口趋势与分析系统"]
    output["CSV 文件 / 分析报告 / 图表 / 答辩材料"]

    admin -->|"登录、采集、维护、分析"| system
    viewer -->|"查询、筛选、统计、预测、导出"| system
    public_source -->|"HTML/CSV/表格数据"| system
    system -->|"预测解释请求"| llm
    llm -->|"解释文本"| system
    system -->|"结果输出"| output
```

## DFD 0 层图

```mermaid
flowchart TB
    user["用户"]
    source["公开统计数据源"]

    p1["P1 登录与权限验证"]
    p2["P2 人口数据采集与管理"]
    p3["P3 查询筛选、排序与对比"]
    p4["P4 统计分析与可视化"]
    p5["P5 机器学习预测与风险评估"]
    p6["P6 成果输出与审计"]

    d1[("D1 users")]
    d2[("D2 population_data")]
    d3[("D3 regions")]
    d4[("D4 data_sources")]
    d5[("D5 population_indicators")]
    d6[("D6 annual_indicator_values")]
    d7[("D7 analysis_reports")]
    d8[("D8 operation_logs")]

    user --> p1
    p1 <--> d1
    p1 --> user

    source --> p2
    user --> p2
    p2 <--> d2
    p2 <--> d3
    p2 <--> d4
    p2 --> d8

    user --> p3
    p3 <--> d2
    p3 --> user

    user --> p4
    p4 <--> d2
    p4 <--> d5
    p4 <--> d6
    p4 --> user

    user --> p5
    p5 <--> d2
    p5 --> user

    user --> p6
    p6 <--> d7
    p6 <--> d8
    p6 -->|"CSV / 报告 / 图表 / 文档"| user
```

## DFD 1 层：人口数据采集与导入

```mermaid
flowchart LR
    admin["管理员"]
    source["公开数据 URL / 粘贴表格"]
    parse["解析 HTML/CSV/表格文本"]
    preview["采集结果预览"]
    validate["字段校验与单位换算"]
    save["写入人口年度数据"]
    source_save["整理数据来源"]
    log["记录操作日志"]

    d2[("population_data")]
    d4[("data_sources")]
    d8[("operation_logs")]

    admin --> source
    source --> parse --> preview --> validate --> save --> d2
    validate --> source_save --> d4
    save --> log --> d8
```

## DFD 1 层：预测、解释与报告输出

```mermaid
flowchart LR
    user["用户"]
    select["选择地区/指标/预测年数"]
    history["读取历史人口数据"]
    model["线性回归 + 增长率拟合"]
    risk["智能风险评估"]
    explain["大模型或本地规则解释"]
    report["保存分析报告"]
    chart["预测图表展示"]

    d2[("population_data")]
    d7[("analysis_reports")]

    user --> select --> history
    history <--> d2
    history --> model --> risk --> explain
    model --> chart --> user
    explain --> user
    explain --> report --> d7
```

## 关系说明

- `users.username` 与 `operation_logs.username`、`analysis_reports.username` 是逻辑关联，用于追踪用户行为和报告归属。
- `regions.name` 与 `population_data.region`、`annual_indicator_values.region` 是逻辑关联，用于地区档案和年度数据的对应。
- `population_indicators.code` 与 `annual_indicator_values.indicator_code` 是外键关系，用于扩展指标定义和值的关联。
- `data_sources` 用于记录公开统计数据来源，与人口数据保持来源说明层面的业务关联。
