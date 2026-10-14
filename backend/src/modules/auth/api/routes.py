from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.modules.auth.application.login import LoginUseCase
from src.modules.auth.infrastructure.repository_credential_checker import (
    RepositoryCredentialChecker,
)
from src.shared.common.errors import ValidationError

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        raise ValidationError("Thiếu tài khoản hoặc mật khẩu")
    use_case = LoginUseCase(RepositoryCredentialChecker())
    result = use_case.execute(username, password)
    return jsonify({"token": result.token, "user_id": result.user_id, "role": result.role})
