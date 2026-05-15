from population_insight.db.connection import execute_write, fetch_all


def log_operation(
    username: str,
    action: str,
    target_id: int | None = None,
    details: str = "",
) -> None:
    execute_write(
        """
        INSERT INTO operation_logs (username, action, target_id, details)
        VALUES (?, ?, ?, ?)
        """,
        (username, action, target_id, details),
    )


def list_operation_logs(limit: int = 30) -> list[dict]:
    return fetch_all(
        """
        SELECT id, username, action, target_id, details, action_time
        FROM operation_logs
        ORDER BY action_time DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    )
