from __future__ import annotations


API_CASES = [
    (
        "/api/dashboard/map?year=2024&metric=total_population",
        {"items", "metric", "metricLabel", "year"},
    ),
    (
        "/api/national-series/trend?metric=total_population",
        {"xAxis", "series", "metricLabel"},
    ),
    (
        "/api/charts/trend?region=北京市&metric=total_population&mode=absolute",
        {"xAxis", "series", "metricLabel", "title"},
    ),
    (
        "/api/charts/bar?year=2024&metric=total_population",
        {"xAxis", "series", "metricLabel", "title"},
    ),
    (
        "/api/charts/gender?region=北京市&year=2024",
        {"labels", "series", "title"},
    ),
    (
        "/api/comparison?regions=全国&regions=北京市&metric=total_population&start_year=2020&end_year=2024",
        {"regions", "series", "latest_rank", "table_rows"},
    ),
    (
        "/api/prediction/chart?region=全国&metric=total_population&forecast_years=5",
        {"xAxis", "history", "prediction", "title"},
    ),
]


def test_core_api_endpoints_return_expected_shapes(admin_client):
    for path, expected_keys in API_CASES:
        response = admin_client.get(path)
        payload = response.get_json()

        assert response.status_code == 200, path
        assert payload["success"] is True, path
        assert expected_keys.issubset(payload["data"].keys()), path


def test_api_validation_errors_are_structured(admin_client):
    response = admin_client.get("/api/charts/bar?year=not-a-year&metric=total_population")
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["success"] is False
    assert payload["message"]
