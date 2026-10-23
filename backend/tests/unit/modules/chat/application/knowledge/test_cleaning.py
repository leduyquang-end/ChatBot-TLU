from src.modules.chat.application.knowledge.cleaning import (
    clean_text,
    strip_cjk,
    strip_repeated_headers,
)


def test_clean_text_chuan_hoa_va_bo_ky_tu_khong_in_duoc():
    assert clean_text("a  b\r\n\r\n\r\n\r\nc\x00") == "a b\n\nc"


def test_strip_repeated_headers_bo_tieu_de_lap_qua_3_lan():
    text = "\n".join(["Trường Đại học Thủy Lợi"] * 4 + ["Điều 1. Nội dung"])
    out = strip_repeated_headers(text)
    assert "Trường Đại học" not in out
    assert "Điều 1. Nội dung" in out


def test_strip_repeated_headers_giu_khi_chua_vuot_3_lan():
    text = "\n".join(["Trường Đại học Thủy Lợi"] * 3 + ["Điều 1. Nội dung"])
    out = strip_repeated_headers(text)
    assert out.count("Trường Đại học Thủy Lợi") == 3


def test_strip_repeated_headers_giu_dong_ngan_lap():
    text = "\n".join(["AB"] * 10 + ["Điều 1. Nội dung"])
    out = strip_repeated_headers(text)
    assert out.count("AB") == 10


def test_strip_cjk_bo_chu_trung_va_gon_khoang_trang():
    assert strip_cjk("khoa đại học负责 quản lý") == "khoa đại học quản lý"
    assert strip_cjk("trực thuộc Trường,负责 GDTC.") == "trực thuộc Trường, GDTC."


def test_strip_cjk_giu_nguyen_tieng_viet():
    assert strip_cjk("Khoa Công nghệ thông tin") == "Khoa Công nghệ thông tin"
