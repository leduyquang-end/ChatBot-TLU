from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.modules.auth.application.login import LoginUseCase
from src.modules.auth.infrastructure.hmac_token_issuer import HmacTokenIssuer
from src.modules.auth.infrastructure.repository_credential_checker import (
    RepositoryCredentialChecker,
)
from src.shared.common.errors import ValidationError

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/login")
def login():
    # Bước 1: Nhận dữ liệu
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    # Bước 2: Kiểm tra thô (thiếu field bắt buộc → ValidationError 400)
    if not isinstance(username, str) or not username.strip():
        raise ValidationError("Thiếu tài khoản hoặc mật khẩu")
    if not isinstance(password, str) or not password:
        raise ValidationError("Thiếu tài khoản hoặc mật khẩu")

    # Bước 3: Gọi use case (logic nghiệp vụ nằm ở LoginUseCase, không ở route)
    use_case = LoginUseCase(
        checker=RepositoryCredentialChecker(),
        token_issuer=HmacTokenIssuer(),
    )
    result = use_case.execute(username.strip(), password)

    # Bước 4: Trả kết quả
    return jsonify(
        {"token": result.token, "user_id": result.user_id, "role": result.role}
    )
