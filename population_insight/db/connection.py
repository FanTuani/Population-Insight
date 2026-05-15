import sqlite3
from typing import Any, Iterable

from population_insight.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def fetch_one(query: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(query, tuple(params or [])).fetchone()
    return dict(row) if row else None


def fetch_all(query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(query, tuple(params or [])).fetchall()
    return [dict(row) for row in rows]


def execute_write(query: str, params: Iterable[Any] | None = None) -> int:
    with get_connection() as connection:
        cursor = connection.execute(query, tuple(params or []))
        connection.commit()
        return cursor.lastrowid


def execute_many(query: str, params_list: Iterable[Iterable[Any]]) -> None:
    with get_connection() as connection:
        connection.executemany(query, params_list)
        connection.commit()
