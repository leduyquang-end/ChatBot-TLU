from src.modules.chat.domain.conversation import Conversation


def make_conversation(turn_pairs: int) -> Conversation:
    conv = Conversation(conversation_id="c1", user_id="u1")
    for i in range(turn_pairs):
        conv.add_turn(f"câu hỏi {i}", f"trả lời {i}")
    return conv


def test_add_turn_them_cap_user_assistant():
    conv = Conversation(conversation_id="c1", user_id="u1")
    conv.add_turn("Chào trường?", "Chào em")
    assert conv.turns == [
        {"role": "user", "content": "Chào trường?"},
        {"role": "assistant", "content": "Chào em"},
    ]


def test_history_giu_du_khi_chua_vuot_max():
    conv = make_conversation(2)
    history = conv.history(max_turns=5)
    assert len(history) == 4
    assert history[0]["content"] == "câu hỏi 0"


def test_history_cat_lay_max_turns_moi_nhat():
    conv = make_conversation(3)
    history = conv.history(max_turns=2)
    assert len(history) == 4
    assert history[0]["content"] == "câu hỏi 1"
    assert history[-1]["content"] == "trả lời 2"


def test_history_max_turns_am_hoac_khong_tra_gi():
    conv = make_conversation(3)
    assert conv.history(max_turns=0) == []
    assert conv.history(max_turns=-1) == []


def test_history_conversation_moi_co_turn_rong():
    conv = Conversation(conversation_id="c1", user_id="u1")
    assert conv.history(max_turns=3) == []
