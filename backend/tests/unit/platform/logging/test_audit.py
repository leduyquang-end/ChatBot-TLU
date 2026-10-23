import logging

from src.platform.logging.audit import register_audit_handlers
from src.shared.events import (
    EventBus,
    KnowledgeIngested,
    UserLoggedIn,
    UserPasswordChanged,
)


def test_dang_ky_lap_lai_khong_tao_handler_trung():
    bus = EventBus()
    register_audit_handlers(bus)
    register_audit_handlers(bus)

    assert bus.publish(UserLoggedIn(user_id="u-1", role="student")) == 1
    assert bus.publish(UserPasswordChanged(user_id="u-1")) == 1
    assert (
        bus.publish(
            KnowledgeIngested(
                chunks=1, entities=2, relations=3, duration_seconds=0.5
            )
        )
        == 1
    )


def test_ghi_log_dang_nhap_thanh_cong(caplog):
    bus = EventBus()
    register_audit_handlers(bus)

    with caplog.at_level(logging.INFO, logger="src.platform.logging.audit"):
        bus.publish(UserLoggedIn(user_id="u-1", role="student"))

    assert "event=audit.user.logged_in" in caplog.text
    assert "user_id=u-1" in caplog.text
    assert "role=student" in caplog.text


def test_ghi_log_doi_mat_khau(caplog):
    bus = EventBus()
    register_audit_handlers(bus)

    with caplog.at_level(logging.INFO, logger="src.platform.logging.audit"):
        bus.publish(UserPasswordChanged(user_id="u-1"))

    assert "event=audit.user.password_changed" in caplog.text
    assert "user_id=u-1" in caplog.text


def test_ghi_log_nap_tri_thuc_chi_kem_so_lieu(caplog):
    bus = EventBus()
    register_audit_handlers(bus)

    with caplog.at_level(logging.INFO, logger="src.platform.logging.audit"):
        bus.publish(
            KnowledgeIngested(
                chunks=10, entities=4, relations=3, duration_seconds=1.25
            )
        )

    assert "event=audit.knowledge.ingested" in caplog.text
    assert "chunks=10" in caplog.text
    assert "entities=4" in caplog.text
    assert "relations=3" in caplog.text
    assert "duration_s=1.25" in caplog.text
