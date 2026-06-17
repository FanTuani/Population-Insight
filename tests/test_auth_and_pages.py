from __future__ import annotations


MAIN_PAGES = [
    "/",
    "/records",
    "/collection",
    "/statistics",
    "/comparison",
    "/prediction",
    "/national-series",
    "/charts",
    "/alerts",
    "/reports",
    "/regions",
    "/sources",
    "/indicators",
    "/logs",
    "/settings",
    "/users",
    "/permissions",
]


def test_login_success_and_failure(client, login):
    assert client.get("/login").status_code == 200

    failed = login("admin", "wrong-password")
    assert failed.status_code == 200
    assert "用户名或密码错误".encode() in failed.data

    success = login("admin", "admin123")
    assert success.status_code == 302
    assert success.headers["Location"].endswith("/")


def test_login_required_redirects_anonymous_users(client):
    response = client.get("/records", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_can_open_main_pages(admin_client):
    for path in MAIN_PAGES:
        response = admin_client.get(path)
        assert response.status_code == 200, path
        assert response.data.strip(), path


def test_viewer_is_blocked_from_admin_pages(viewer_client):
    for path in ("/users", "/permissions", "/settings", "/logs", "/regions", "/sources", "/indicators"):
        response = viewer_client.get(path, follow_redirects=False)
        assert response.status_code == 302, path
        assert response.headers["Location"].endswith("/")


def test_logout_clears_session(admin_client):
    response = admin_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
