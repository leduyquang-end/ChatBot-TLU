from __future__ import annotations

import logging
import time

import requests

from src.modules.chat.domain.prompt import SERVICE_BUSY_MESSAGE
from src.shared.common.errors import ExternalServiceError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
NO_RETRY_STATUS = {401, 403}


def post_json_with_retry(
    url: str,
    *,
    service: str,
    headers: dict,
    payload: dict,
    timeout: float,
    max_retries: int,
    backoff_seconds: float,
) -> requests.Response:
    """POST JSON, thử lại tối đa `max_retries` lần cho lỗi tạm thời (AGENT mục 7.1).

    - Tạm thời (timeout, lỗi kết nối, HTTP 429/5xx): thử lại, chờ tăng dần.
    - Xác thực (401/403): dừng ngay, ghi log, không thử lại.
    - Lỗi client khác (4xx): dừng ngay, không thử lại.
    - Hết lượt thử: ném ExternalServiceError với thông báo tạm thời cho người dùng.
    """
    total_attempts = 1 + max(0, max_retries)
    last_reason = ""
    for attempt in range(1, total_attempts + 1):
        started = time.monotonic()
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            last_reason = type(exc).__name__
        else:
            duration_ms = int((time.monotonic() - started) * 1000)
            status = response.status_code
            if status < 400:
                return response
            last_reason = f"http_{status}"
            if status in NO_RETRY_STATUS:
                logger.error(
                    "event=chat.service.auth_error service=%s status=%s duration_ms=%s",
                    service,
                    status,
                    duration_ms,
                )
                raise ExternalServiceError(
                    SERVICE_BUSY_MESSAGE, detail=f"{service}: HTTP {status}"
                )
            if status not in RETRYABLE_STATUS:
                logger.error(
                    "event=chat.service.error service=%s status=%s duration_ms=%s",
                    service,
                    status,
                    duration_ms,
                )
                raise ExternalServiceError(
                    SERVICE_BUSY_MESSAGE, detail=f"{service}: HTTP {status}"
                )
        if attempt >= total_attempts:
            break
        wait = backoff_seconds * (2 ** (attempt - 1))
        logger.warning(
            "event=chat.service.retry service=%s attempt=%s reason=%s backoff_s=%.1f",
            service,
            attempt,
            last_reason,
            wait,
        )
        time.sleep(wait)
    logger.error(
        "event=chat.service.failed service=%s attempts=%s reason=%s",
        service,
        total_attempts,
        last_reason,
    )
    raise ExternalServiceError(
        SERVICE_BUSY_MESSAGE, detail=f"{service}: {last_reason}"
    )
