from __future__ import annotations

from pathlib import Path

from population_insight.services.collection_service import (
    collect_population_records_from_file,
    import_collected_records,
)
from population_insight.services.export_service import export_to_csv
from population_insight.services.population_service import (
    add_population_record,
    delete_population_record,
    get_population_record_by_id,
    query_population_records,
    sort_population_records,
    update_population_record,
)


def _new_record(year: int = 2030) -> dict:
    return {
        "region": "测试省",
        "year": year,
        "total_population": 10_000_000,
        "male_population": 5_100_000,
        "female_population": 4_900_000,
        "birth_rate": 7.2,
        "death_rate": 5.1,
        "natural_growth_rate": 2.1,
        "aging_rate": 18.5,
        "urbanization_rate": 66.6,
        "remarks": "自动化测试记录",
    }


def test_population_crud_filter_and_sort_workflow():
    record_id = add_population_record(_new_record(), username="pytest")
    created = get_population_record_by_id(record_id)

    assert created["region"] == "测试省"
    assert created["year"] == 2030

    update_population_record(
        record_id,
        {**_new_record(), "total_population": 11_000_000, "male_population": 5_600_000, "female_population": 5_400_000},
        username="pytest",
    )
    updated = get_population_record_by_id(record_id)
    assert updated["total_population"] == 11_000_000

    filtered = query_population_records({"region": "测试", "year": 2030})
    assert [item["id"] for item in filtered] == [record_id]

    sorted_records = sort_population_records(filtered + query_population_records({"region": "北京市"}), "year", "desc")
    assert sorted_records[0]["year"] >= sorted_records[-1]["year"]

    delete_population_record(record_id, username="pytest")
    assert get_population_record_by_id(record_id) is None


def test_csv_import_preview_and_import_workflow():
    csv_content = (
        "地区,年份,总人口,男性人口,女性人口,出生率,死亡率,老龄化率,城镇化率,备注\n"
        "测试市,2031,1000000,510000,490000,8.1,5.0,16.2,70.5,CSV导入测试\n"
    ).encode("utf-8-sig")
    preview = collect_population_records_from_file("sample.csv", csv_content)

    assert preview["record_count"] == 1
    assert preview["records"][0]["region"] == "测试市"

    result = import_collected_records(preview["records"], username="pytest")
    assert result == {"imported": 1, "failed": 0, "errors": []}
    assert query_population_records({"region": "测试市", "year": 2031})


def test_export_to_csv_creates_readable_file(tmp_path):
    records = query_population_records({"region": "北京市", "year": 2024})
    output_path = tmp_path / "beijing_export.csv"

    exported = Path(export_to_csv(records, str(output_path)))

    assert exported.exists()
    text = exported.read_text(encoding="utf-8-sig")
    assert "region" in text
    assert "北京市" in text
