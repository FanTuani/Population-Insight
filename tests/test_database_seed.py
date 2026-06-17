from __future__ import annotations

from population_insight.db.connection import fetch_all, fetch_one


def test_seeded_database_counts_match_readme():
    counts = {
        name: fetch_one(f"SELECT COUNT(*) AS count FROM {name}")["count"]
        for name in (
            "users",
            "population_data",
            "national_population_series",
            "regions",
            "data_sources",
            "population_indicators",
            "annual_indicator_values",
            "analysis_reports",
        )
    }

    assert counts["users"] == 2
    assert counts["population_data"] == 310
    assert counts["national_population_series"] == 76
    assert counts["regions"] == 31
    assert counts["data_sources"] == 31
    assert counts["population_indicators"] >= 3
    assert counts["annual_indicator_values"] >= 6
    assert counts["analysis_reports"] >= 0


def test_seeded_year_ranges_and_region_coverage():
    national = fetch_one(
        "SELECT MIN(year) AS min_year, MAX(year) AS max_year, COUNT(*) AS count "
        "FROM national_population_series"
    )
    provincial = fetch_one(
        "SELECT COUNT(DISTINCT region) AS regions, MIN(year) AS min_year, "
        "MAX(year) AS max_year, COUNT(*) AS count FROM population_data"
    )
    users = fetch_all("SELECT username, role FROM users ORDER BY username")

    assert national == {"min_year": 1950, "max_year": 2025, "count": 76}
    assert provincial == {"regions": 31, "min_year": 2015, "max_year": 2024, "count": 310}
    assert users == [
        {"username": "admin", "role": "admin"},
        {"username": "viewer", "role": "viewer"},
    ]
