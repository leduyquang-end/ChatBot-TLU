from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.modules.auth.application.login import LoginUseCase
from src.modules.auth.application.logout import LogoutUseCase
from src.modules.auth.application.refresh import RefreshTokenUseCase
from src.modules.auth.infrastructure.hmac_token_issuer import HmacTokenIssuer
from src.modules.auth.infrastructure.in_memory_refresh_token_store import (
    get_refresh_token_store,
)
from src.modules.auth.infrastructure.repository_credential_checker import (
    RepositoryCredentialChecker,
)
from src.modules.user.infrastructure.in_memory_user_repository import (
    get_user_repository,
)
from src.shared.common.errors import ValidationError

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _read_refresh_token() -> str:
    """Nhận + kiểm tra thô refresh_token (400 nếu thiếu/sai kiểu) — dùng chung cho refresh và logout."""
    data = request.get_json(silent=True) or {}
    raw = data.get("refresh_token")
    if not isinstance(raw, str) or not raw.strip():
        raise ValidationError("Thiếu refresh_token")
    return raw.strip()


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
        store=get_refresh_token_store(),
    )
    result = use_case.execute(username.strip(), password)

    # Bước 4: Trả kết quả
    return jsonify(
        {
            "token": result.token,
            "refresh_token": result.refresh_token,
            "user_id": result.user_id,
            "role": result.role,
        }
    )


@bp.post("/refresh")
def refresh():
    # Bước 1-2: Nhận dữ liệu + kiểm tra thô
    raw = _read_refresh_token()

    # Bước 3: Gọi use case
    use_case = RefreshTokenUseCase(
        store=get_refresh_token_store(),
        token_issuer=HmacTokenIssuer(),
        users=get_user_repository(),
    )
    result = use_case.execute(raw)

    # Bước 4: Trả kết quả
    return jsonify(
        {
            "token": result.token,
            "refresh_token": result.refresh_token,
            "user_id": result.user_id,
            "role": result.role,
        }
    )


@bp.post("/logout")
def logout():
    # Bước 1-2: Nhận dữ liệu + kiểm tra thô
    raw = _read_refresh_token()

    # Bước 3: Gọi use case
    use_case = LogoutUseCase(store=get_refresh_token_store())
    result = use_case.execute(raw)

    # Bước 4: Trả kết quả
    return jsonify({"revoked": result.revoked})
