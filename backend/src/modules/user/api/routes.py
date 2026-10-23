from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.modules.user.application.change_password import ChangePassword
from src.modules.user.application.get_user_by_id import GetUserById
from src.modules.user.application.list_users import ListUsers
from src.modules.user.application.update_my_profile import UpdateMyProfile
from src.modules.user.domain.user import FULL_NAME_MAX_LENGTH, ROLE_ADMIN, User
from src.modules.user.infrastructure.in_memory_user_repository import (
    get_user_repository,
)
from src.platform.security.auth import require_role, sanitize_input, verify_token
from src.shared.common.errors import UnauthorizedError, ValidationError
from src.shared.events import get_event_bus

bp = Blueprint("user", __name__, url_prefix="/user")


def _current_user() -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError("Cần đăng nhập")
    user_id = verify_token(auth.removeprefix("Bearer ").strip())
    return GetUserById(get_user_repository()).execute(user_id)


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _serialize(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }


@bp.get("/me")
def get_me():
    return jsonify(_serialize(_current_user()))


@bp.put("/me")
def update_me():
    me = _current_user()
    raw_full_name = _json_body().get("full_name")
    if not isinstance(raw_full_name, str):
        raise ValidationError("Họ và tên không được để trống")
    full_name = sanitize_input(raw_full_name, max_length=FULL_NAME_MAX_LENGTH + 1)
    updated = UpdateMyProfile(get_user_repository()).execute(me.id, full_name)
    return jsonify(_serialize(updated))


@bp.post("/change-password")
def change_password():
    me = _current_user()
    data = _json_body()
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not isinstance(old_password, str) or not old_password:
        raise ValidationError("Thiếu mật khẩu cũ")
    if not isinstance(new_password, str) or not new_password:
        raise ValidationError("Thiếu mật khẩu mới")
    ChangePassword(get_user_repository(), get_event_bus()).execute(me.id, old_password, new_password)
    return jsonify({"changed": True})


@bp.get("")
def list_users():
    me = _current_user()
    require_role(me.role, {ROLE_ADMIN})
    users = ListUsers(get_user_repository()).execute()
    return jsonify({"users": [_serialize(user) for user in users]})
