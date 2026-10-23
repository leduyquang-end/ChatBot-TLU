import threading

from src.shared.events import (
    Event,
    EventBus,
    UserLoggedIn,
    UserPasswordChanged,
    get_event_bus,
    reset_event_bus,
)


def test_publish_goi_handler_cung_loai():
    bus = EventBus()
    seen = []
    bus.subscribe(UserLoggedIn, seen.append)
    called = bus.publish(UserLoggedIn(user_id="u-001", role="student"))
    assert called == 1
    assert [event.user_id for event in seen] == ["u-001"]


def test_khong_co_handler_tra_0():
    assert EventBus().publish(UserLoggedIn(user_id="u", role="student")) == 0


def test_khong_gui_sang_loai_khac():
    bus = EventBus()
    seen = []
    bus.subscribe(UserLoggedIn, seen.append)
    called = bus.publish(UserPasswordChanged(user_id="u-001"))
    assert called == 0
    assert seen == []


def test_subscribe_trung_chi_chay_mot_lan():
    bus = EventBus()
    seen = []
    bus.subscribe(UserLoggedIn, seen.append)
    bus.subscribe(UserLoggedIn, seen.append)
    assert bus.publish(UserLoggedIn(user_id="u", role="student")) == 1
    assert len(seen) == 1


def test_unsubscribe_ngung_nhan_va_idempotent():
    bus = EventBus()
    seen = []
    handler = seen.append
    bus.subscribe(UserLoggedIn, handler)
    bus.unsubscribe(UserLoggedIn, handler)
    assert bus.publish(UserLoggedIn(user_id="u", role="student")) == 0
    bus.unsubscribe(UserLoggedIn, handler)  # gọi lặp lại không lỗi
    assert seen == []


def test_handler_loi_khong_lam_hong_handler_khac():
    bus = EventBus()
    seen = []

    def bad(_event):
        raise RuntimeError("handler lỗi")

    bus.subscribe(UserLoggedIn, bad)
    bus.subscribe(UserLoggedIn, seen.append)
    assert bus.publish(UserLoggedIn(user_id="u-001", role="student")) == 2
    assert len(seen) == 1


def test_publish_tu_nhieu_thread():
    bus = EventBus()
    lock = threading.Lock()
    count = 0

    def count_up(_event):
        nonlocal count
        with lock:
            count += 1

    bus.subscribe(UserLoggedIn, count_up)
    threads = [
        threading.Thread(
            target=bus.publish,
            args=(UserLoggedIn(user_id=f"u-{i}", role="student"),),
        )
        for i in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert count == 8


def test_singleton_va_reset():
    first = get_event_bus()
    assert get_event_bus() is first
    reset_event_bus()
    try:
        assert get_event_bus() is not first
    finally:
        reset_event_bus()


def test_chi_gui_dung_loai_chinh_xac():
    bus = EventBus()
    seen = []
    bus.subscribe(Event, seen.append)
    assert bus.publish(UserLoggedIn(user_id="u", role="student")) == 0
    assert seen == []


def test_unsubscribe_loai_chua_dang_ky_khong_loi():
    EventBus().unsubscribe(UserLoggedIn, lambda _event: None)


def test_bus_singleton_an_toan_nhieu_thread():
    reset_event_bus()
    results = []
    lock = threading.Lock()

    def grab():
        bus = get_event_bus()
        with lock:
            results.append(id(bus))

    threads = [threading.Thread(target=grab) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    try:
        assert len(set(results)) == 1
    finally:
        reset_event_bus()


def test_clear_goa_het_dang_ky():
    bus = EventBus()
    seen = []
    bus.subscribe(UserLoggedIn, seen.append)
    bus.clear()
    assert bus.publish(UserLoggedIn(user_id="u", role="student")) == 0
