from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from population_insight.config import DB_ENGINE, DB_PATH, MYSQL_CONFIG


class DatabaseConfigError(RuntimeError):
    """Raised when the selected database backend is not configured correctly."""


class MySQLConnectionAdapter:
    def __init__(self, raw_connection):
        self._connection = raw_connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self._connection.rollback()
        self._connection.close()

    def execute(self, query: str, params: Iterable[Any] | None = None):
        cursor = self._connection.cursor()
        cursor.execute(_translate_query(query), tuple(params or []))
        return cursor

    def executemany(self, query: str, params_list: Iterable[Iterable[Any]]) -> None:
        cursor = self._connection.cursor()
        cursor.executemany(_translate_query(query), list(params_list))

    def executescript(self, script: str) -> None:
        for statement in _split_sql_script(script):
            self.execute(statement)

    def commit(self) -> None:
        self._connection.commit()


def _split_sql_script(script: str) -> list[str]:
    return [statement.strip() for statement in script.split(";") if statement.strip()]


def is_mysql() -> bool:
    return DB_ENGINE == "mysql"


def get_integrity_error_types() -> tuple[type[BaseException], ...]:
    if is_mysql():
        try:
            import pymysql
        except ImportError:
            return ()
        return (pymysql.err.IntegrityError,)
    return (sqlite3.IntegrityError,)


def is_unique_constraint_error(error: BaseException) -> bool:
    message = str(error).lower()
    return (
        "unique constraint failed" in message
        or "duplicate entry" in message
        or "1062" in message
    )


def _translate_query(query: str) -> str:
    if not is_mysql():
        return query
    return query.replace("?", "%s")


def get_connection():
    if is_mysql():
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as error:
            raise DatabaseConfigError(
                "MySQL mode requires PyMySQL. Install dependencies with: pip install -r requirements.txt"
            ) from error

        raw_connection = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"],
            charset=MYSQL_CONFIG["charset"],
            cursorclass=DictCursor,
            autocommit=False,
        )
        return MySQLConnectionAdapter(raw_connection)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def execute_query(connection, query: str, params: Iterable[Any] | None = None):
    return connection.execute(_translate_query(query), tuple(params or []))


def execute_many_query(connection, query: str, params_list: Iterable[Iterable[Any]]) -> None:
    connection.executemany(_translate_query(query), params_list)


def fetch_one(query: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = execute_query(connection, query, params).fetchone()
    return dict(row) if row else None


def fetch_all(query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = execute_query(connection, query, params).fetchall()
    return [dict(row) for row in rows]


def execute_write(query: str, params: Iterable[Any] | None = None) -> int:
    with get_connection() as connection:
        cursor = execute_query(connection, query, params)
        connection.commit()
        return cursor.lastrowid


def execute_many(query: str, params_list: Iterable[Iterable[Any]]) -> None:
    with get_connection() as connection:
        execute_many_query(connection, query, params_list)
        connection.commit()
