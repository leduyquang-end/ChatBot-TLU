from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RefreshToken:
    """Phiên làm việc để lấy lại token mới mà không phải đăng nhập lại.

    - Bất biến (frozen): sau khi tạo, không sửa được — muốn đổi thì tạo phiên mới.
    - So sánh theo giá trị: 2 phiên giống hệt nhau về mọi trường là một phiên.
    - Luật nghiệp vụ "hết hạn" nằm trong chính object (is_expired), không rải ra nơi khác.
    """

    token: str
    user_id: str
    issued_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        """Hết hạn khi thời điểm kiểm tra >= thời điểm hết hạn (hết hạn ngay tại mốc)."""
        return now >= self.expires_at
