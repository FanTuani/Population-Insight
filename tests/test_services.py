from __future__ import annotations

import pytest

from population_insight.services.comparison_service import build_region_comparison
from population_insight.services.extension_service import get_population_alerts
from population_insight.services.national_series_service import (
    build_national_population_prediction,
    get_national_series_summary,
    get_national_trend_data,
)
from population_insight.services.prediction_service import build_population_prediction
from population_insight.services.statistics_service import calculate_statistics, get_region_ranking
from population_insight.utils.validators import validate_population_payload


def test_statistics_ranking_and_alerts_are_available():
    statistics = calculate_statistics(region="北京市", start_year=2015, end_year=2024)
    ranking = get_region_ranking(metric="total_population", year=2024, top_n=5)
    alerts = get_population_alerts()

    assert statistics["record_count"] == 10
    assert statistics["avg_total_population"] > 0
    assert len(ranking) == 5
    assert alerts


def test_comparison_and_prediction_services_return_chart_data():
    comparison = build_region_comparison(
        regions=["全国", "北京市"],
        metric="total_population",
        start_year=2020,
        end_year=2024,
    )
    provincial_prediction = build_population_prediction("北京市", "total_population", forecast_years=3)
    national_prediction = build_national_population_prediction(forecast_years=3)

    assert comparison["regions"] == ["全国", "北京市"]
    assert comparison["series"]
    assert provincial_prediction["chart"]["prediction"]
    assert len(national_prediction["predictions"]) == 3


def test_national_series_summary_and_trend_data():
    summary = get_national_series_summary()
    trend = get_national_trend_data("total_population")

    assert summary["min_year"] == 1950
    assert summary["max_year"] == 2025
    assert summary["total_years"] == 76
    assert len(trend["xAxis"]) == 76
    assert len(trend["series"]) == 76


def test_population_payload_validation_rejects_invalid_data():
    with pytest.raises(ValueError):
        validate_population_payload(
            {
                "region": "错误省",
                "year": 2030,
                "total_population": 100,
                "male_population": 80,
                "female_population": 80,
                "birth_rate": 1,
                "death_rate": 1,
                "aging_rate": 1,
                "urbanization_rate": 1,
            }
        )
