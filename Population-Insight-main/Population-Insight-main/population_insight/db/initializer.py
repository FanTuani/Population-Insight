from population_insight.config import (
    CHART_DIR,
    DATA_DIR,
    DEFAULT_USERS,
    EXPORT_DIR,
    INITIAL_ANNUAL_INDICATOR_VALUES,
    INITIAL_DATA_SOURCES,
    INITIAL_POPULATION_INDICATORS,
    INITIAL_POPULATION_RECORDS,
    INITIAL_REGIONS,
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
                aging_rate_basis TEXT DEFAULT '60_plus',
                data_source_name TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                data_quality TEXT DEFAULT '',
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

            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                region_type TEXT NOT NULL,
                admin_code TEXT DEFAULT '',
                parent_region TEXT DEFAULT '',
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                publisher TEXT NOT NULL,
                source_url TEXT DEFAULT '',
                published_date TEXT DEFAULT '',
                reliability_level TEXT NOT NULL DEFAULT '中',
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS population_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS annual_indicator_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                year INTEGER NOT NULL,
                indicator_code TEXT NOT NULL,
                value REAL NOT NULL,
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region, year, indicator_code),
                FOREIGN KEY(indicator_code) REFERENCES population_indicators(code)
            );

            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                username TEXT NOT NULL,
                filter_summary TEXT DEFAULT '',
                report_summary TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()


def ensure_population_data_columns() -> None:
    expected_columns = {
        "aging_rate_basis": "TEXT DEFAULT '60_plus'",
        "data_source_name": "TEXT DEFAULT ''",
        "source_url": "TEXT DEFAULT ''",
        "data_quality": "TEXT DEFAULT ''",
    }
    with get_connection() as connection:
        existing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(population_data)").fetchall()
        }
        for column, definition in expected_columns.items():
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE population_data ADD COLUMN {column} {definition}")
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
            record.get("aging_rate_basis", "60_plus"),
            record.get("data_source_name", ""),
            record.get("source_url", ""),
            record.get("data_quality", ""),
            record["remarks"],
        )
        for record in INITIAL_POPULATION_RECORDS
    ]


def seed_sample_data() -> None:
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
                aging_rate_basis,
                data_source_name,
                source_url,
                data_quality,
                remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _build_sample_records(),
        )
        connection.commit()


def seed_extension_data() -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO regions (name, region_type, admin_code, parent_region, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    item["name"],
                    item["region_type"],
                    item["admin_code"],
                    item["parent_region"],
                    item["remarks"],
                )
                for item in INITIAL_REGIONS
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO data_sources (
                name, publisher, source_url, published_date, reliability_level, remarks
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["name"],
                    item["publisher"],
                    item["source_url"],
                    item["published_date"],
                    item["reliability_level"],
                    item["remarks"],
                )
                for item in INITIAL_DATA_SOURCES
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO population_indicators (code, name, unit, description)
            VALUES (?, ?, ?, ?)
            """,
            [
                (item["code"], item["name"], item["unit"], item["description"])
                for item in INITIAL_POPULATION_INDICATORS
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO annual_indicator_values (
                region, year, indicator_code, value, remarks
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    item["region"],
                    item["year"],
                    item["indicator_code"],
                    item["value"],
                    item["remarks"],
                )
                for item in INITIAL_ANNUAL_INDICATOR_VALUES
            ],
        )
        connection.commit()


def init_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    create_tables()
    ensure_population_data_columns()
    seed_users()
    seed_sample_data()
    seed_extension_data()
