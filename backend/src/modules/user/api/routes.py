from __future__ import annotations

from flask import Blueprint, jsonify

from src.modules.user.application.get_user_by_id import GetUserById
from src.modules.user.infrastructure.in_memory_user_repository import (
    get_user_repository,
)

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.get("/me")
def get_me():
    from flask import request

    from src.platform.security.auth import verify_token

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Cần đăng nhập"}}), 401
    user_id = verify_token(auth.removeprefix("Bearer ").strip())
    use_case = GetUserById(get_user_repository())
    user = use_case.execute(user_id)
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
        }
    )
