import logging

import pytest

from src.platform.logging.setup import (
    get_logger,
    log_event,
    reset_logging,
    setup_logging,
)


@pytest.fixture(autouse=True)
def _clean_state():
    reset_logging()
    yield
    reset_logging()


def event_lines(output: str, marker: str = "event=") -> list[str]:
    return [line for line in output.splitlines() if marker in line]


def test_setup_khong_lap_handler():
    """Gọi lần hai bị bỏ qua — chỉ một handler, mức không bị đổi (một lần khi khởi động)."""
    setup_logging("INFO")
    setup_logging("DEBUG")
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.INFO


def test_setup_force_cau_hinh_lai():
    setup_logging("INFO")
    setup_logging("WARNING", force=True)
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.WARNING


def test_setup_level_sai_fall_back_info():
    setup_logging("LEVEL_KHONG_TON_TAI", force=True)
    assert logging.getLogger().level == logging.INFO


def test_reset_cho_phep_cau_hinh_lai():
    setup_logging("INFO")
    reset_logging()
    setup_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_reset_tra_muc_mac_dinh_warning():
    setup_logging("INFO")
    reset_logging()
    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger().handlers == []


def test_get_logger_ten_dung():
    assert get_logger("abc.def").name == "abc.def"


def test_log_event_dinh_dang_mot_dong(capsys):
    setup_logging("INFO")
    log_event(
        get_logger("test.mod"),
        logging.INFO,
        "chat.router.selected",
        mode="Vector",
        turns=3,
    )
    lines = event_lines(capsys.readouterr().out, marker="event=chat.router.selected")
    assert len(lines) == 1
    assert "level=INFO" in lines[0]
    assert "mode=Vector" in lines[0]
    assert "turns=3" in lines[0]


def test_log_event_che_khoa_nhay_cam(capsys):
    setup_logging("INFO")
    log_event(
        get_logger("t"),
        logging.INFO,
        "user.login",
        username="sv01",
        password="mat-khau-1",
        api_key="sk-123",
        access_token="eyJhbGciOi",
    )
    out = capsys.readouterr().out
    assert "mat-khau-1" not in out
    assert "sk-123" not in out
    assert "eyJhbGciOi" not in out
    assert out.count("[REDACTED]") == 3
    assert "username=sv01" in out


def test_log_event_che_lung_dict_list(capsys):
    """Khóa nhạy cảm bị bắt cả khi nằm trong dict/list lồng nhau."""
    setup_logging("INFO")
    log_event(
        get_logger("t"),
        logging.INFO,
        "service.call",
        headers={"Authorization": "Bearer x.y.z"},
        data={"user_password": "abc123"},
        items=[{"email": "a@b.c"}],
    )
    out = capsys.readouterr().out
    assert "Bearer x.y.z" not in out
    assert "abc123" not in out
    assert "a@b.c" not in out


def test_log_event_khong_che_id_cuoc_hoi(capsys):
    """AGENT.md 10.2: mã định danh cuộc trò chuyện, cách tìm được phép ghi."""
    setup_logging("INFO")
    log_event(
        get_logger("t"),
        logging.INFO,
        "chat.ask",
        conversation_id="c-123",
        mode="Graph",
    )
    out = capsys.readouterr().out
    assert "conversation_id=c-123" in out
    assert "mode=Graph" in out


def test_log_event_gia_tri_nhieu_dong_van_mot_dong(capsys):
    """Mỗi dòng một sự kiện — giá trị nhiều dòng không được phá vỡ định dạng."""
    setup_logging("INFO")
    log_event(get_logger("t"), logging.ERROR, "app.detail", detail="dong 1\ndong 2")
    lines = event_lines(capsys.readouterr().out, marker="event=app.detail")
    assert len(lines) == 1
    assert "dong 1\\ndong 2" in lines[0]


def test_log_event_gia_tri_co_khoang_trang_duoc_ngoac_kep(capsys):
    setup_logging("INFO")
    log_event(get_logger("t"), logging.INFO, "e.spaces", detail="cau tra loi")
    lines = event_lines(capsys.readouterr().out, marker="event=e.spaces")
    assert len(lines) == 1
    assert 'detail="cau tra loi"' in lines[0]


def test_log_event_khoa_khong_hop_le_duoc_don_rui(capsys):
    setup_logging("INFO")
    log_event(get_logger("t"), logging.INFO, "e.weird", **{"user name": "x"})
    out = capsys.readouterr().out
    assert "user_name=x" in out


def test_log_event_nhan_level_dang_chuoi(capsys):
    """Cho phép level dạng chuỗi ('WARNING') thay vì hằng int."""
    setup_logging("INFO")
    log_event(get_logger("t"), "WARNING", "e.str", ok=1)
    lines = event_lines(capsys.readouterr().out, marker="event=e.str")
    assert len(lines) == 1
    assert "level=WARNING" in lines[0]


def test_log_event_none_va_bool(capsys):
    setup_logging("INFO")
    log_event(get_logger("t"), logging.INFO, "e.types", note=None, ok=True)
    out = capsys.readouterr().out
    assert "note=-" in out
    assert "ok=true" in out
