from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TEST_TMP_DIR = ROOT_DIR / ".tmp" / "pytest"
TEST_DB_PATH = TEST_TMP_DIR / "population_insight_test.db"
SEED_DB_PATH = TEST_TMP_DIR / "population_insight_seed.db"
TEST_OUTPUT_DIR = TEST_TMP_DIR / "output"

os.environ["POPULATION_INSIGHT_DB_ENGINE"] = "sqlite"
os.environ["POPULATION_INSIGHT_DB_PATH"] = str(TEST_DB_PATH)
os.environ["POPULATION_INSIGHT_OUTPUT_DIR"] = str(TEST_OUTPUT_DIR)


def _remove_sqlite_files(base_path: Path) -> None:
    for suffix in ("", "-shm", "-wal", "-journal"):
        path = Path(f"{base_path}{suffix}")
        if path.exists():
            path.unlink()


def _ensure_seed_database() -> None:
    TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if SEED_DB_PATH.exists():
        return

    _remove_sqlite_files(TEST_DB_PATH)

    from population_insight.db.initializer import init_database

    init_database()
    shutil.copy2(TEST_DB_PATH, SEED_DB_PATH)


@pytest.fixture(autouse=True)
def fresh_database():
    _ensure_seed_database()
    _remove_sqlite_files(TEST_DB_PATH)
    shutil.copy2(SEED_DB_PATH, TEST_DB_PATH)
    yield


@pytest.fixture
def app_instance():
    from app import app

    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


@pytest.fixture
def login(client):
    def _login(username: str = "admin", password: str = "admin123"):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    return _login


@pytest.fixture
def admin_client(client, login):
    response = login("admin", "admin123")
    assert response.status_code == 302
    return client


@pytest.fixture
def viewer_client(client, login):
    response = login("viewer", "viewer123")
    assert response.status_code == 302
    return client
