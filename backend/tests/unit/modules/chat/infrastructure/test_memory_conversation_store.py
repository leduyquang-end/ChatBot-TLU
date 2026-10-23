from src.modules.chat.infrastructure.memory_conversation_store import (
    InMemoryConversationStore,
)


def test_get_or_create_id_moi_chua_tu_luu_vao_store():
    store = InMemoryConversationStore()
    conv = store.get_or_create("c1", "u1")
    assert conv.conversation_id == "c1"
    assert conv.user_id == "u1"
    # chưa save → không nằm trong store (hỏi với id lạ không phình bộ nhớ)
    assert store.list_for_user("u1") == []


def test_sau_save_lay_lai_duoc_cung_conversation():
    store = InMemoryConversationStore()
    conv = store.get_or_create("c1", "u1")
    conv.add_turn("Học phí?", "Trả lời")
    store.save(conv)

    again = store.get_or_create("c1", "u1")
    assert again is conv
    assert len(again.turns) == 2


def test_id_thuoc_user_khac_tra_conversation_moi_khac_id():
    store = InMemoryConversationStore()
    mine = store.get_or_create("c-priv", "u1")
    mine.add_turn("Câu của u1", "Trả lời của u1")
    store.save(mine)

    other = store.get_or_create("c-priv", "u2")
    assert other is not mine
    assert other.conversation_id != "c-priv"
    assert other.user_id == "u2"
    assert other.turns == []
    # conversation gốc không bị đụng tới
    assert len(mine.turns) == 2
    assert mine.user_id == "u1"


def test_id_la_voi_cung_user_van_tao_conversation_moi_chua_luu():
    store = InMemoryConversationStore()
    first = store.get_or_create("moi", "u1")
    first.add_turn("q", "a")
    store.save(first)

    fresh = store.get_or_create("khong-ton-tai", "u1")
    assert fresh.conversation_id == "khong-ton-tai"
    assert fresh.turns == []
    assert store.list_for_user("u1") == [first]


def test_list_for_user_loc_theo_chu():
    store = InMemoryConversationStore()
    a = store.get_or_create("c1", "u1")
    store.save(a)
    b = store.get_or_create("c2", "u2")
    store.save(b)
    c = store.get_or_create("c3", "u1")
    store.save(c)

    assert sorted(x.conversation_id for x in store.list_for_user("u1")) == ["c1", "c3"]
    assert [x.conversation_id for x in store.list_for_user("u2")] == ["c2"]
    assert store.list_for_user("u3") == []
