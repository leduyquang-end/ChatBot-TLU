import pytest

from src.shared.common.errors import (
    AppError,
    ConfigError,
    ExternalServiceError,
    ForbiddenError,
    InternalError,
    NoRelevantContextError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


@pytest.mark.parametrize(
    "cls,code,status",
    [
        (ValidationError, "VALIDATION_ERROR", 400),
        (UnauthorizedError, "UNAUTHORIZED", 401),
        (ForbiddenError, "FORBIDDEN", 403),
        (NotFoundError, "NOT_FOUND", 404),
        (ExternalServiceError, "EXTERNAL_SERVICE_ERROR", 503),
        (NoRelevantContextError, "NO_RELEVANT_CONTEXT", 200),
        (ConfigError, "CONFIG_ERROR", 500),
        (InternalError, "INTERNAL_ERROR", 500),
    ],
)
def test_bang_loi_theo_readme(cls, code, status):
    """Đối chiếu đúng bảng lỗi trong common/README.md."""
    err = cls("Thông điệp mô tả")
    assert isinstance(err, AppError)
    assert err.code == code
    assert err.http_status == status
    assert err.message == "Thông điệp mô tả"


def test_app_error_mac_dinh_message_la_code():
    err = AppError()
    assert err.code == "INTERNAL_ERROR"
    assert err.message == "INTERNAL_ERROR"


def test_app_error_co_detail():
    err = ValidationError("Sai", detail="truong=ten")
    assert err.detail == "truong=ten"
    assert AppError("x").detail is None
