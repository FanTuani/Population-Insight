from population_insight.config import (
    CHART_DIR,
    DATA_DIR,
    DEFAULT_USERS,
    EXPORT_DIR,
    INITIAL_POPULATION_RECORDS,
)
from population_insight.db.connection import fetch_one, get_connection
from population_insight.utils.security import hash_password


def create_tables() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'viewer')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS population_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                year INTEGER NOT NULL,
                total_population INTEGER NOT NULL CHECK(total_population >= 0),
                male_population INTEGER NOT NULL CHECK(male_population >= 0),
                female_population INTEGER NOT NULL CHECK(female_population >= 0),
                birth_rate REAL NOT NULL CHECK(birth_rate >= 0),
                death_rate REAL NOT NULL CHECK(death_rate >= 0),
                natural_growth_rate REAL NOT NULL,
                aging_rate REAL NOT NULL CHECK(aging_rate >= 0),
                urbanization_rate REAL NOT NULL CHECK(urbanization_rate >= 0),
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region, year)
            );

            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                details TEXT DEFAULT '',
                action_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()


def seed_users() -> None:
    user_rows = [
        (user["username"], hash_password(user["password"]), user["role"])
        for user in DEFAULT_USERS
    ]
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            user_rows,
        )
        connection.commit()


def _build_sample_records() -> list[tuple]:
    return [
        (
            record["region"],
            record["year"],
            record["total_population"],
            record["male_population"],
            record["female_population"],
            record["birth_rate"],
            record["death_rate"],
            record["natural_growth_rate"],
            record["aging_rate"],
            record["urbanization_rate"],
            record["remarks"],
        )
        for record in INITIAL_POPULATION_RECORDS
    ]


def seed_sample_data() -> None:
    existing = fetch_one("SELECT COUNT(*) AS count FROM population_data")
    if existing and existing["count"] > 0:
        return

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO population_data (
                region,
                year,
                total_population,
                male_population,
                female_population,
                birth_rate,
                death_rate,
                natural_growth_rate,
                aging_rate,
                urbanization_rate,
                remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _build_sample_records(),
        )
        connection.commit()


def init_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    create_tables()
    seed_users()
    seed_sample_data()
