from population_insight.db.connection import fetch_one
from population_insight.services.log_service import log_operation
from population_insight.utils.security import verify_password


def login(username: str, password: str) -> dict | None:
    user = fetch_one(
        """
        SELECT id, username, password_hash, role, created_at
        FROM users
        WHERE username = ?
        """,
        (username.strip(),),
    )
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        log_operation(user["username"], "LOGIN_FAILED", details="密码错误")
        return None

    log_operation(user["username"], "LOGIN_SUCCESS", target_id=user["id"])
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
    }
