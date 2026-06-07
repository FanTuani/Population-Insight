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
from population_insight.db.connection import fetch_one, get_connection, is_mysql
from population_insight.services.national_series_service import build_seed_records
from population_insight.utils.security import hash_password


def create_tables() -> None:
    if is_mysql():
        create_mysql_tables()
        return

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

            CREATE TABLE IF NOT EXISTS national_population_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL UNIQUE,
                total_population INTEGER NOT NULL CHECK(total_population >= 0),
                birth_rate REAL,
                death_rate REAL,
                natural_growth_rate REAL,
                urban_population INTEGER CHECK(urban_population IS NULL OR urban_population >= 0),
                urbanization_rate REAL,
                source_name TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                data_quality TEXT DEFAULT '',
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()


def create_mysql_tables() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK(role IN ('admin', 'viewer'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS population_data (
                id INT PRIMARY KEY AUTO_INCREMENT,
                region VARCHAR(100) NOT NULL,
                year INT NOT NULL,
                total_population BIGINT NOT NULL CHECK(total_population >= 0),
                male_population BIGINT NOT NULL CHECK(male_population >= 0),
                female_population BIGINT NOT NULL CHECK(female_population >= 0),
                birth_rate DOUBLE NOT NULL CHECK(birth_rate >= 0),
                death_rate DOUBLE NOT NULL CHECK(death_rate >= 0),
                natural_growth_rate DOUBLE NOT NULL,
                aging_rate DOUBLE NOT NULL CHECK(aging_rate >= 0),
                urbanization_rate DOUBLE NOT NULL CHECK(urbanization_rate >= 0),
                aging_rate_basis VARCHAR(50) DEFAULT '60_plus',
                data_source_name VARCHAR(255) DEFAULT '',
                source_url TEXT,
                data_quality VARCHAR(100) DEFAULT '',
                remarks TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_population_region_year (region, year)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS operation_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(100) NOT NULL,
                action VARCHAR(100) NOT NULL,
                target_id INT,
                details TEXT,
                action_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS regions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                region_type VARCHAR(100) NOT NULL,
                admin_code VARCHAR(50) DEFAULT '',
                parent_region VARCHAR(100) DEFAULT '',
                remarks TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS data_sources (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                publisher VARCHAR(255) NOT NULL,
                source_url TEXT,
                published_date VARCHAR(30) DEFAULT '',
                reliability_level VARCHAR(20) NOT NULL DEFAULT '中',
                remarks TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS population_indicators (
                id INT PRIMARY KEY AUTO_INCREMENT,
                code VARCHAR(100) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                unit VARCHAR(50) NOT NULL,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS annual_indicator_values (
                id INT PRIMARY KEY AUTO_INCREMENT,
                region VARCHAR(100) NOT NULL,
                year INT NOT NULL,
                indicator_code VARCHAR(100) NOT NULL,
                value DOUBLE NOT NULL,
                remarks TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_annual_indicator (region, year, indicator_code),
                CONSTRAINT fk_annual_indicator_code
                    FOREIGN KEY(indicator_code) REFERENCES population_indicators(code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INT PRIMARY KEY AUTO_INCREMENT,
                title VARCHAR(255) NOT NULL,
                username VARCHAR(100) NOT NULL,
                filter_summary TEXT,
                report_summary TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS national_population_series (
                id INT PRIMARY KEY AUTO_INCREMENT,
                year INT NOT NULL UNIQUE,
                total_population BIGINT NOT NULL CHECK(total_population >= 0),
                birth_rate DOUBLE,
                death_rate DOUBLE,
                natural_growth_rate DOUBLE,
                urban_population BIGINT CHECK(urban_population IS NULL OR urban_population >= 0),
                urbanization_rate DOUBLE,
                source_name VARCHAR(255) DEFAULT '',
                source_url TEXT,
                data_quality VARCHAR(100) DEFAULT '',
                remarks TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        connection.commit()


def _insert_ignore_sql(table_and_columns: str, placeholders: str) -> str:
    if is_mysql():
        return f"INSERT IGNORE INTO {table_and_columns} VALUES ({placeholders})"
    return f"INSERT OR IGNORE INTO {table_and_columns} VALUES ({placeholders})"


def _population_data_upsert_sql() -> str:
    base_insert = """
            INSERT INTO population_data (
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
    """
    if is_mysql():
        return (
            base_insert
            + """
            ON DUPLICATE KEY UPDATE
                total_population = VALUES(total_population),
                male_population = VALUES(male_population),
                female_population = VALUES(female_population),
                birth_rate = VALUES(birth_rate),
                death_rate = VALUES(death_rate),
                natural_growth_rate = VALUES(natural_growth_rate),
                aging_rate = VALUES(aging_rate),
                urbanization_rate = VALUES(urbanization_rate),
                aging_rate_basis = VALUES(aging_rate_basis),
                data_source_name = VALUES(data_source_name),
                source_url = VALUES(source_url),
                data_quality = VALUES(data_quality),
                remarks = VALUES(remarks),
                updated_at = CURRENT_TIMESTAMP
            """
        )
    return (
        base_insert
        + """
            ON CONFLICT(region, year) DO UPDATE SET
                total_population = excluded.total_population,
                male_population = excluded.male_population,
                female_population = excluded.female_population,
                birth_rate = excluded.birth_rate,
                death_rate = excluded.death_rate,
                natural_growth_rate = excluded.natural_growth_rate,
                aging_rate = excluded.aging_rate,
                urbanization_rate = excluded.urbanization_rate,
                aging_rate_basis = excluded.aging_rate_basis,
                data_source_name = excluded.data_source_name,
                source_url = excluded.source_url,
                data_quality = excluded.data_quality,
                remarks = excluded.remarks,
                updated_at = CURRENT_TIMESTAMP
            """
    )


def _national_series_upsert_sql() -> str:
    base_insert = """
            INSERT INTO national_population_series (
                year,
                total_population,
                birth_rate,
                death_rate,
                natural_growth_rate,
                urban_population,
                urbanization_rate,
                source_name,
                source_url,
                data_quality,
                remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    if is_mysql():
        return (
            base_insert
            + """
            ON DUPLICATE KEY UPDATE
                total_population = VALUES(total_population),
                birth_rate = VALUES(birth_rate),
                death_rate = VALUES(death_rate),
                natural_growth_rate = VALUES(natural_growth_rate),
                urban_population = VALUES(urban_population),
                urbanization_rate = VALUES(urbanization_rate),
                source_name = VALUES(source_name),
                source_url = VALUES(source_url),
                data_quality = VALUES(data_quality),
                remarks = VALUES(remarks),
                updated_at = CURRENT_TIMESTAMP
            """
        )
    return (
        base_insert
        + """
            ON CONFLICT(year) DO UPDATE SET
                total_population = excluded.total_population,
                birth_rate = excluded.birth_rate,
                death_rate = excluded.death_rate,
                natural_growth_rate = excluded.natural_growth_rate,
                urban_population = excluded.urban_population,
                urbanization_rate = excluded.urbanization_rate,
                source_name = excluded.source_name,
                source_url = excluded.source_url,
                data_quality = excluded.data_quality,
                remarks = excluded.remarks,
                updated_at = CURRENT_TIMESTAMP
            """
    )


def ensure_population_data_columns() -> None:
    expected_columns = (
        {
            "aging_rate_basis": "VARCHAR(50) DEFAULT '60_plus'",
            "data_source_name": "VARCHAR(255) DEFAULT ''",
            "source_url": "TEXT",
            "data_quality": "VARCHAR(100) DEFAULT ''",
        }
        if is_mysql()
        else {
            "aging_rate_basis": "TEXT DEFAULT '60_plus'",
            "data_source_name": "TEXT DEFAULT ''",
            "source_url": "TEXT DEFAULT ''",
            "data_quality": "TEXT DEFAULT ''",
        }
    )
    with get_connection() as connection:
        if is_mysql():
            rows = connection.execute("SHOW COLUMNS FROM population_data").fetchall()
            existing_columns = {row["Field"] for row in rows}
        else:
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
            _insert_ignore_sql("users (username, password_hash, role)", "?, ?, ?"),
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
            _population_data_upsert_sql(),
            _build_sample_records(),
        )
        connection.commit()


def seed_extension_data() -> None:
    with get_connection() as connection:
        connection.executemany(
            _insert_ignore_sql(
                "regions (name, region_type, admin_code, parent_region, remarks)",
                "?, ?, ?, ?, ?",
            ),
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
            _insert_ignore_sql(
                "data_sources (name, publisher, source_url, published_date, reliability_level, remarks)",
                "?, ?, ?, ?, ?, ?",
            ),
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
            _insert_ignore_sql("population_indicators (code, name, unit, description)", "?, ?, ?, ?"),
            [
                (item["code"], item["name"], item["unit"], item["description"])
                for item in INITIAL_POPULATION_INDICATORS
            ],
        )
        connection.executemany(
            _insert_ignore_sql(
                "annual_indicator_values (region, year, indicator_code, value, remarks)",
                "?, ?, ?, ?, ?",
            ),
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


def seed_national_series() -> None:
    existing = fetch_one(
        """
        SELECT COUNT(*) AS count, MIN(year) AS min_year, MAX(year) AS max_year
        FROM national_population_series
        """
    )
    if (
        existing
        and existing.get("count", 0) >= 76
        and existing.get("min_year") == 1950
        and existing.get("max_year") == 2025
    ):
        return

    records = build_seed_records()
    with get_connection() as connection:
        connection.executemany(
            _national_series_upsert_sql(),
            [
                (
                    item["year"],
                    item["total_population"],
                    item.get("birth_rate"),
                    item.get("death_rate"),
                    item.get("natural_growth_rate"),
                    item.get("urban_population"),
                    item.get("urbanization_rate"),
                    item.get("source_name", ""),
                    item.get("source_url", ""),
                    item.get("data_quality", ""),
                    item.get("remarks", ""),
                )
                for item in records
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
    seed_national_series()
