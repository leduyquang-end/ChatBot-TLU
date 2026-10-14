from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify

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
from src.platform.logging.setup import setup_logging
from src.shared.common.errors import AppError
from src.shared.config.settings import get_settings

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    settings = get_settings()
    setup_logging(settings.log_level)

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

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        logger.error("event=chat.internal.error type=%s", type(exc).__name__)
        return (
            jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Hệ thống đang gặp sự cố"}}),
            500,
        )

    logger.info("event=app.started port=%s", settings.app_port)
    return app


# Gunicorn entrypoint: src.main:app (cần biến môi trường đã nạp)
app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    app.run(host="0.0.0.0", port=settings.app_port, debug=False)
