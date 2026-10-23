from __future__ import annotations


class AppError(Exception):
    """Lỗi nghiệp vụ cơ sở. Domain và application chỉ ném loại này."""

    code = "INTERNAL_ERROR"
    http_status = 500

    def __init__(self, message: str = "", *, detail: str | None = None) -> None:
        super().__init__(message or self.code)
        self.message = message or self.code
        self.detail = detail


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    http_status = 400


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    http_status = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    http_status = 403


class NotFoundError(AppError):
    code = "NOT_FOUND"
    http_status = 404


class ExternalServiceError(AppError):
    code = "EXTERNAL_SERVICE_ERROR"
    http_status = 503


class InternalError(AppError):
    """Lỗi không mong đợi — đã ghi log, người dùng chỉ thấy thông báo chung."""

    code = "INTERNAL_ERROR"
    http_status = 500


class NoRelevantContextError(AppError):
    """Không có thông tin phù hợp trong kho tri thức (ADR-09)."""

    code = "NO_RELEVANT_CONTEXT"
    http_status = 200


class ConfigError(AppError):
    """Thiếu hoặc sai cấu hình khi khởi động."""

    code = "CONFIG_ERROR"
    http_status = 500
