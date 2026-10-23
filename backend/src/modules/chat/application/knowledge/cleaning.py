from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    """Bỏ khoảng trắng thừa, ký tự không mang nghĩa."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "".join(ch for ch in text if ch == "\n" or ch.isprintable())
    return text.strip()


_CJK_PATTERN = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")


def strip_cjk(text: str) -> str:
    """Bỏ ký tự Trung/Nhật/Hàn — LLM đôi khi lẫn vào tên/mô tả thực thể."""
    return re.sub(r"\s{2,}", " ", _CJK_PATTERN.sub(" ", text)).strip()


def strip_repeated_headers(text: str, *, max_repeat: int = 3) -> str:
    """Bỏ tiêu đề/chân trang lặp lại nhiều lần."""
    lines = text.split("\n")
    counts: dict[str, int] = {}
    for line in lines:
        key = line.strip()
        if len(key) >= 10:
            counts[key] = counts.get(key, 0) + 1
    kept = [
        line
        for line in lines
        if not (len(line.strip()) >= 10 and counts.get(line.strip(), 0) > max_repeat)
    ]
    return "\n".join(kept)
