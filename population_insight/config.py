from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CHART_DIR = OUTPUT_DIR / "charts"
EXPORT_DIR = OUTPUT_DIR / "exports"
DB_PATH = DATA_DIR / "population_insight.db"
FLASK_SECRET_KEY = "population-insight-course-design"
WEB_PAGE_SIZE = 10

YEAR_MIN = 2000
YEAR_MAX = 2035

DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "viewer", "password": "viewer123", "role": "viewer"},
]

ALLOWED_SORT_FIELDS = {
    "id": "id",
    "region": "region",
    "year": "year",
    "total_population": "total_population",
    "birth_rate": "birth_rate",
    "death_rate": "death_rate",
    "natural_growth_rate": "natural_growth_rate",
    "aging_rate": "aging_rate",
    "urbanization_rate": "urbanization_rate",
}

METRIC_LABELS = {
    "total_population": "总人口",
    "male_population": "男性人口",
    "female_population": "女性人口",
    "birth_rate": "出生率",
    "death_rate": "死亡率",
    "natural_growth_rate": "自然增长率",
    "aging_rate": "老龄化率",
    "urbanization_rate": "城镇化率",
}

def _to_people(ten_thousand_people: float) -> int:
    return int(round(ten_thousand_people * 10000))


def _record(
    *,
    region: str,
    year: int,
    total_population_10k: float,
    male_population_10k: float,
    female_population_10k: float,
    birth_rate: float,
    death_rate: float,
    natural_growth_rate: float,
    aging_rate: float,
    urbanization_rate: float,
    remarks: str,
) -> dict:
    return {
        "region": region,
        "year": year,
        "total_population": _to_people(total_population_10k),
        "male_population": _to_people(male_population_10k),
        "female_population": _to_people(female_population_10k),
        "birth_rate": round(birth_rate, 2),
        "death_rate": round(death_rate, 2),
        "natural_growth_rate": round(natural_growth_rate, 2),
        "aging_rate": round(aging_rate, 2),
        "urbanization_rate": round(urbanization_rate, 2),
        "remarks": remarks,
    }


INITIAL_POPULATION_RECORDS = [
    _record(
        region="北京市",
        year=2015,
        total_population_10k=2188.3,
        male_population_10k=1126.2,
        female_population_10k=1062.1,
        birth_rate=7.89,
        death_rate=4.91,
        natural_growth_rate=2.98,
        aging_rate=16.73,
        urbanization_rate=86.71,
        remarks="依据北京统计年鉴2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2016,
        total_population_10k=2195.4,
        male_population_10k=1126.1,
        female_population_10k=1069.3,
        birth_rate=9.23,
        death_rate=5.16,
        natural_growth_rate=4.07,
        aging_rate=17.25,
        urbanization_rate=86.76,
        remarks="依据北京统计年鉴2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2017,
        total_population_10k=2194.4,
        male_population_10k=1123.9,
        female_population_10k=1070.5,
        birth_rate=8.97,
        death_rate=5.24,
        natural_growth_rate=3.73,
        aging_rate=17.98,
        urbanization_rate=86.93,
        remarks="依据北京统计年鉴2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2018,
        total_population_10k=2191.7,
        male_population_10k=1122.2,
        female_population_10k=1069.5,
        birth_rate=8.13,
        death_rate=5.50,
        natural_growth_rate=2.63,
        aging_rate=18.60,
        urbanization_rate=87.09,
        remarks="依据北京统计年鉴2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2019,
        total_population_10k=2190.1,
        male_population_10k=1120.5,
        female_population_10k=1069.6,
        birth_rate=7.98,
        death_rate=5.40,
        natural_growth_rate=2.58,
        aging_rate=19.10,
        urbanization_rate=87.35,
        remarks="依据北京统计年鉴2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2020,
        total_population_10k=2189.0,
        male_population_10k=1119.4,
        female_population_10k=1069.6,
        birth_rate=6.98,
        death_rate=4.59,
        natural_growth_rate=2.39,
        aging_rate=19.64,
        urbanization_rate=87.55,
        remarks="依据北京统计年鉴2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2021,
        total_population_10k=2188.6,
        male_population_10k=1117.7,
        female_population_10k=1070.9,
        birth_rate=6.35,
        death_rate=5.39,
        natural_growth_rate=0.96,
        aging_rate=20.18,
        urbanization_rate=87.55,
        remarks="依据北京统计公报2021整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2022,
        total_population_10k=2184.3,
        male_population_10k=1117.0,
        female_population_10k=1067.3,
        birth_rate=5.67,
        death_rate=5.72,
        natural_growth_rate=-0.05,
        aging_rate=21.29,
        urbanization_rate=87.60,
        remarks="依据北京市2022年统计公报及公开人口统计整理，性别人数按公开占比折算，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2023,
        total_population_10k=2185.8,
        male_population_10k=1113.3,
        female_population_10k=1072.5,
        birth_rate=5.63,
        death_rate=6.13,
        natural_growth_rate=-0.50,
        aging_rate=22.64,
        urbanization_rate=87.80,
        remarks="依据2023年统计公报及中国统计年鉴2024整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="北京市",
        year=2024,
        total_population_10k=2183.2,
        male_population_10k=1111.3,
        female_population_10k=1071.9,
        birth_rate=6.09,
        death_rate=6.08,
        natural_growth_rate=0.01,
        aging_rate=23.54,
        urbanization_rate=88.20,
        remarks="依据统计公报2024整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="广东省",
        year=2020,
        total_population_10k=12624.0,
        male_population_10k=6699.56,
        female_population_10k=5924.44,
        birth_rate=10.28,
        death_rate=4.70,
        natural_growth_rate=5.58,
        aging_rate=12.35,
        urbanization_rate=74.15,
        remarks="依据广东统计年鉴2022及第七次全国人口普查公报整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="广东省",
        year=2021,
        total_population_10k=12684.0,
        male_population_10k=6693.0,
        female_population_10k=5991.0,
        birth_rate=9.35,
        death_rate=4.83,
        natural_growth_rate=4.52,
        aging_rate=12.73,
        urbanization_rate=74.63,
        remarks="依据2021年广东统计公报及人口结构分析整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="广东省",
        year=2022,
        total_population_10k=12656.8,
        male_population_10k=6673.8,
        female_population_10k=5983.0,
        birth_rate=8.30,
        death_rate=4.97,
        natural_growth_rate=3.33,
        aging_rate=13.45,
        urbanization_rate=74.79,
        remarks="依据2022年广东省国民经济和社会发展统计公报整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="广东省",
        year=2023,
        total_population_10k=12706.0,
        male_population_10k=6689.0,
        female_population_10k=6017.0,
        birth_rate=8.12,
        death_rate=5.36,
        natural_growth_rate=2.76,
        aging_rate=14.24,
        urbanization_rate=75.42,
        remarks="依据2023年统计公报、中国统计年鉴2024及老龄人口公开报道整理，老龄化率按60岁及以上常住人口占比。",
    ),
    _record(
        region="广东省",
        year=2024,
        total_population_10k=12780.0,
        male_population_10k=6728.0,
        female_population_10k=6052.0,
        birth_rate=8.89,
        death_rate=5.20,
        natural_growth_rate=3.69,
        aging_rate=14.86,
        urbanization_rate=75.91,
        remarks="依据2024年广东省国民经济和社会发展统计公报整理，老龄化率按60岁及以上常住人口占比。",
    ),
]

INITIAL_REGIONS = [
    {
        "name": "北京市",
        "region_type": "直辖市",
        "admin_code": "110000",
        "parent_region": "中国",
        "remarks": "国家中心城市，人口结构变化具有代表性。",
    },
    {
        "name": "广东省",
        "region_type": "省",
        "admin_code": "440000",
        "parent_region": "中国",
        "remarks": "常住人口规模长期位居全国前列。",
    },
]

INITIAL_DATA_SOURCES = [
    {
        "name": "北京市人口统计",
        "publisher": "北京市人民政府",
        "source_url": "https://www.beijing.gov.cn/renwen/bjgk/rk/rktj/",
        "published_date": "2025-03-01",
        "reliability_level": "高",
        "remarks": "用于北京市人口年度数据核验。",
    },
    {
        "name": "广东省统计公报",
        "publisher": "广东省统计局",
        "source_url": "https://stats.gd.gov.cn/",
        "published_date": "2025-03-01",
        "reliability_level": "高",
        "remarks": "用于广东省人口年度数据核验。",
    },
]

INITIAL_POPULATION_INDICATORS = [
    {
        "code": "child_ratio",
        "name": "少儿人口占比",
        "unit": "%",
        "description": "0-14岁人口占常住人口比重。",
    },
    {
        "code": "working_age_ratio",
        "name": "劳动年龄人口占比",
        "unit": "%",
        "description": "15-59岁人口占常住人口比重。",
    },
    {
        "code": "dependency_ratio",
        "name": "总抚养比",
        "unit": "%",
        "description": "少儿与老年人口对劳动年龄人口的比例。",
    },
]

INITIAL_ANNUAL_INDICATOR_VALUES = [
    {"region": "北京市", "year": 2024, "indicator_code": "child_ratio", "value": 11.2, "remarks": "样例扩展指标。"},
    {"region": "北京市", "year": 2024, "indicator_code": "working_age_ratio", "value": 65.3, "remarks": "样例扩展指标。"},
    {"region": "北京市", "year": 2024, "indicator_code": "dependency_ratio", "value": 53.1, "remarks": "样例扩展指标。"},
    {"region": "广东省", "year": 2024, "indicator_code": "child_ratio", "value": 18.6, "remarks": "样例扩展指标。"},
    {"region": "广东省", "year": 2024, "indicator_code": "working_age_ratio", "value": 66.5, "remarks": "样例扩展指标。"},
    {"region": "广东省", "year": 2024, "indicator_code": "dependency_ratio", "value": 50.4, "remarks": "样例扩展指标。"},
]
