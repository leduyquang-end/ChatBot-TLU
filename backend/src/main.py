from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

# Đọc .env trước khi load settings (ưu tiên .env ở repo root, fallback backend/)
try:
    from dotenv import load_dotenv

    _here = Path(__file__).resolve()
    for _candidate in (_here.parents[2] / ".env", _here.parents[1] / ".env"):
        if _candidate.exists():
            load_dotenv(_candidate)
            break
except ImportError:
    pass

from src.modules.auth.api.routes import bp as auth_bp
from src.modules.chat.api.routes import bp as chat_bp
from src.modules.user.api.routes import bp as user_bp
from src.platform.logging.audit import register_audit_handlers
from src.platform.logging.setup import get_logger, log_event, setup_logging
from src.shared.common.errors import AppError, InternalError
from src.shared.config.settings import get_settings
from src.shared.events import get_event_bus

logger = get_logger(__name__)


def create_app() -> Flask:
    settings = get_settings()
    setup_logging(settings.log_level)
    register_audit_handlers(get_event_bus())

    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return (
            jsonify({"error": {"code": exc.code, "message": exc.message}}),
            exc.http_status,
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        # Giữ nguyên 404/405... thay vì để handler Exception bên dưới biến thành 500.
        code = (exc.name or "HTTP_ERROR").upper().replace(" ", "_")
        return (
            jsonify({"error": {"code": code, "message": exc.description or ""}}),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        log_event(logger, logging.ERROR, "app.internal.error", type=type(exc).__name__)
        error = InternalError("Hệ thống đang gặp sự cố")
        return (
            jsonify({"error": {"code": error.code, "message": error.message}}),
            error.http_status,
        )

    log_event(logger, logging.INFO, "app.started", port=settings.app_port)
    return app


# Gunicorn entrypoint: src.main:app (cần biến môi trường đã nạp)
app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    app.run(host="0.0.0.0", port=settings.app_port, debug=False)
