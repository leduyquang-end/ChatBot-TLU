from src.modules.chat.application.chat_pipeline import ChatPipeline
from src.modules.chat.domain.conversation import Conversation
from src.modules.chat.domain.retrieval_mode import RetrievalMode
from src.modules.chat.domain.retrieval_result import (
    GraphContext,
    RetrievedChunk,
    RetrievedContext,
)
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings


def make_settings(**overrides) -> Settings:
    base = {
        "groq_api_key": "g",
        "qwen_api_key": "q",
        "hf_token": "h",
        "chroma_url": "http://localhost:8000",
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "pw",
        "no_info_threshold": 0.15,
    }
    base.update(overrides)
    return Settings(**base)


class FakeRouter:
    def __init__(self, mode: RetrievalMode) -> None:
        self._mode = mode

    def classify(self, question: str) -> RetrievalMode:
        return self._mode


class FakeVector:
    def __init__(self, context: RetrievedContext) -> None:
        self._context = context

    def retrieve(self, question: str, *, fetch_k: int, top_k: int) -> RetrievedContext:
        return self._context


class FakeGraph:
    def retrieve(self, question: str, *, alpha: float, fetch_k: int) -> RetrievedContext:
        return RetrievedContext(mode="Graph")


class FailingGraph:
    """Neo4j lỗi: ném ExternalServiceError như infrastructure thật."""

    def retrieve(self, question: str, *, alpha: float, fetch_k: int) -> RetrievedContext:
        raise ExternalServiceError("Kho quan hệ không truy cập được")


class FakeAnswer:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "Câu trả lời từ tài liệu."


class FakeStore:
    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}

    def get_or_create(self, conversation_id: str, user_id: str):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                conversation_id=conversation_id, user_id=user_id
            )
        return self.conversations[conversation_id]

    def save(self, conversation) -> None:
        self.conversations[conversation.conversation_id] = conversation

    def list_for_user(self, user_id: str):
        return [c for c in self.conversations.values() if c.user_id == user_id]


def build_pipeline(
    mode: RetrievalMode,
    context: RetrievedContext,
    generator: FakeAnswer,
    graph_retrieval=None,
):
    return ChatPipeline(
        router=FakeRouter(mode),
        vector_retrieval=FakeVector(context),
        graph_retrieval=graph_retrieval or FakeGraph(),
        answer_generator=generator,
        conversation_store=FakeStore(),
        settings=make_settings(),
    )


def test_ac01_tra_loi_co_tai_lieu():
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Học phí 1.000.000đ", score=0.9, source="HP")],
    )
    generator = FakeAnswer()
    pipeline = build_pipeline(RetrievalMode.VECTOR, context, generator)
    result = pipeline.ask(
        user_id="u1", conversation_id="c1", question="Học phí bao nhiêu?"
    )
    assert result["answer"] == "Câu trả lời từ tài liệu."
    assert len(generator.prompts) == 1
    assert "Học phí bao nhiêu?" in generator.prompts[0]


def test_ac02_khong_goi_mo_hinh_khi_khong_co_thong_tin():
    context = RetrievedContext(mode="Vector")
    generator = FakeAnswer()
    pipeline = build_pipeline(RetrievalMode.VECTOR, context, generator)
    result = pipeline.ask(
        user_id="u1", conversation_id="c1", question="Câu hỏi ngoài tài liệu?"
    )
    assert "chưa có thông tin" in result["answer"]
    assert generator.prompts == []


def test_mode_none_loi_chao_goi_model_khong_tra_no_info():
    """QT-01: 'Không cần tìm' vẫn soạn câu trả lời, không phải thông báo thiếu tin."""
    generator = FakeAnswer()
    pipeline = build_pipeline(
        RetrievalMode.NONE, RetrievedContext(mode="None"), generator
    )
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Xin chào")
    assert result["answer"] == "Câu trả lời từ tài liệu."
    assert len(generator.prompts) == 1
    assert "không truy xuất" in generator.prompts[0]
    assert result["sources"] == []
    assert result["mode"] == "None"


def test_ac03_router_sai_ve_vector_van_tra_loi():
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Nội dung", score=0.9)],
    )
    generator = FakeAnswer()
    pipeline = build_pipeline(RetrievalMode.VECTOR, context, generator)
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Hỏi")
    assert result["mode"] == "Vector"
    assert result["answer"]


def test_ac04_ngu_canh_trong_cung_conversation():
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Ngành CNTT", score=0.9)],
    )
    generator = FakeAnswer()
    store = FakeStore()
    pipeline = ChatPipeline(
        router=FakeRouter(RetrievalMode.VECTOR),
        vector_retrieval=FakeVector(context),
        graph_retrieval=FakeGraph(),
        answer_generator=generator,
        conversation_store=store,
        settings=make_settings(),
    )
    pipeline.ask(user_id="u1", conversation_id="c1", question="Ngành nào?")
    pipeline.ask(user_id="u1", conversation_id="c1", question="Còn học phí sao?")
    second_prompt = generator.prompts[1]
    assert "Ngành nào?" in second_prompt
    assert "Còn học phí sao?" in second_prompt


def build_failing_graph_pipeline(mode: RetrievalMode, generator: FakeAnswer):
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Điều 1: học phí", score=0.9, source="QĐ-01")],
    )
    return ChatPipeline(
        router=FakeRouter(mode),
        vector_retrieval=FakeVector(context),
        graph_retrieval=FailingGraph(),
        answer_generator=generator,
        conversation_store=FakeStore(),
        settings=make_settings(),
    )


def test_neo4j_loi_mode_graph_fallback_ve_vector():
    """Mục 7.2: Neo4j lỗi → vẫn trả lời được bằng Vector, người dùng không thấy lỗi."""
    generator = FakeAnswer()
    pipeline = build_failing_graph_pipeline(RetrievalMode.GRAPH, generator)
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Quyết định X?")
    assert result["mode"] == "Graph"
    assert result["answer"] == "Câu trả lời từ tài liệu."
    assert result["sources"] == ["QĐ-01"]
    assert len(generator.prompts) == 1


def test_neo4j_loi_mode_hybrid_giu_vector_chunks():
    generator = FakeAnswer()
    pipeline = build_failing_graph_pipeline(RetrievalMode.HYBRID, generator)
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Câu hỏi phức tạp?")
    assert result["mode"] == "Hybrid"
    assert result["answer"] == "Câu trả lời từ tài liệu."
    assert result["sources"] == ["QĐ-01"]


def test_history_nguoi_khac_khong_xem_duoc():
    context = RetrievedContext(
        mode="Vector",
        chunks=[RetrievedChunk(text="Nội dung", score=0.9)],
    )
    store = FakeStore()
    pipeline = ChatPipeline(
        router=FakeRouter(RetrievalMode.VECTOR),
        vector_retrieval=FakeVector(context),
        graph_retrieval=FakeGraph(),
        answer_generator=FakeAnswer(),
        conversation_store=store,
        settings=make_settings(),
    )
    pipeline.ask(user_id="u1", conversation_id="c1", question="Câu hỏi của u1?")
    assert pipeline.history(user_id="u1", conversation_id="c1") != []
    assert pipeline.history(user_id="u2", conversation_id="c1") == []


class FakeGraphWithData:
    def __init__(self, nodes, edges=None) -> None:
        self.calls: list[dict] = []
        self._context = RetrievedContext(
            mode="Graph",
            graph=GraphContext(nodes=nodes, edges=edges or []),
        )

    def retrieve(self, question: str, *, alpha: float, fetch_k: int) -> RetrievedContext:
        self.calls.append({"alpha": alpha, "fetch_k": fetch_k})
        return self._context


GRAPH_NODES = [
    {"name": "Học phí", "description": "Mức học phí", "entity_type": "chu_de", "score": 0.9}
]
GRAPH_EDGES = [
    {"source": "Học phí", "target": "Sinh viên", "description": "ảnh hưởng", "confidence": 0.9}
]


def test_graph_mode_giu_graph_vao_prompt():
    generator = FakeAnswer()
    pipeline = build_pipeline(
        RetrievalMode.GRAPH,
        RetrievedContext(mode="Graph"),
        generator,
        graph_retrieval=FakeGraphWithData(GRAPH_NODES, GRAPH_EDGES),
    )
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Học phí?")
    assert result["answer"] == "Câu trả lời từ tài liệu."
    prompt = generator.prompts[0]
    assert "[Thực thể 1] (chu_de) Học phí: Mức học phí" in prompt
    assert "[Quan hệ 1] Học phí → Sinh viên: ảnh hưởng" in prompt


def test_hybrid_gop_vector_chunks_va_graph():
    generator = FakeAnswer()
    context = RetrievedContext(
        mode="Hybrid",
        chunks=[RetrievedChunk(text="Điều 1", score=0.9, source="QĐ-01")],
    )
    pipeline = ChatPipeline(
        router=FakeRouter(RetrievalMode.HYBRID),
        vector_retrieval=FakeVector(context),
        graph_retrieval=FakeGraphWithData(GRAPH_NODES, GRAPH_EDGES),
        answer_generator=generator,
        conversation_store=FakeStore(),
        settings=make_settings(),
    )
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Câu hỏi phức tạp?")
    assert result["mode"] == "Hybrid"
    assert result["sources"] == ["QĐ-01"]
    prompt = generator.prompts[0]
    assert "[Đoạn 1]" in prompt
    assert "[Thực thể 1]" in prompt
    assert "[Quan hệ 1]" in prompt


def test_graph_truyen_alpha_va_fetch_k_theo_settings():
    settings = make_settings()
    graph = FakeGraphWithData(GRAPH_NODES, GRAPH_EDGES)
    generator = FakeAnswer()
    pipeline = ChatPipeline(
        router=FakeRouter(RetrievalMode.GRAPH),
        vector_retrieval=FakeVector(RetrievedContext(mode="Graph")),
        graph_retrieval=graph,
        answer_generator=generator,
        conversation_store=FakeStore(),
        settings=settings,
    )
    pipeline.ask(user_id="u1", conversation_id="c1", question="Học phí?")
    assert graph.calls == [{"alpha": settings.alpha, "fetch_k": settings.fetch_k}]


def test_graph_diem_duoi_nguong_tra_no_info_khong_go_mo_hinh():
    low_nodes = [{"name": "Rác", "description": "", "entity_type": "", "score": 0.05}]
    generator = FakeAnswer()
    pipeline = build_pipeline(
        RetrievalMode.GRAPH,
        RetrievedContext(mode="Graph"),
        generator,
        graph_retrieval=FakeGraphWithData(low_nodes),
    )
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Hỏi ngoài tài liệu?")
    assert "chưa có thông tin" in result["answer"]
    assert generator.prompts == []


def test_ask_id_conversation_cua_user_khac_tao_conversation_moi():
    """user B truyền id của A: không đọc lịch sử A, không ghi vào hội thoại A."""
    from src.modules.chat.infrastructure.memory_conversation_store import (
        InMemoryConversationStore,
    )

    store = InMemoryConversationStore()
    generator = FakeAnswer()
    pipeline = ChatPipeline(
        router=FakeRouter(RetrievalMode.VECTOR),
        vector_retrieval=FakeVector(
            RetrievedContext(
                mode="Vector",
                chunks=[RetrievedChunk(text="Nội dung", score=0.9)],
            )
        ),
        graph_retrieval=FakeGraph(),
        answer_generator=generator,
        conversation_store=store,
        settings=make_settings(),
    )

    first = pipeline.ask(user_id="u1", conversation_id="c-priv", question="Câu hỏi của A?")
    assert first["conversation_id"] == "c-priv"

    second = pipeline.ask(user_id="u2", conversation_id="c-priv", question="Câu hỏi của B?")
    assert second["conversation_id"] != "c-priv"

    # prompt của B không chứa lịch sử A
    assert "Câu hỏi của A?" not in generator.prompts[1]
    # lịch sử A nguyên vẹn, không dính câu của B
    history_u1 = pipeline.history(user_id="u1", conversation_id="c-priv")
    assert [t["content"] for t in history_u1] == ["Câu hỏi của A?", first["answer"]]
    # B vẫn có lịch sử của chính mình qua id mới
    history_u2 = pipeline.history(user_id="u2", conversation_id=second["conversation_id"])
    assert [t["content"] for t in history_u2] == ["Câu hỏi của B?", second["answer"]]


def test_sources_khong_trung_lap_vi_tri_giu_nguyen():
    context = RetrievedContext(
        mode="Vector",
        chunks=[
            RetrievedChunk(text="đoạn 1", score=0.9, source="QĐ-01"),
            RetrievedChunk(text="đoạn 2", score=0.8, source="QĐ-01"),
            RetrievedChunk(text="đoạn 3", score=0.7, source="QĐ-02"),
            RetrievedChunk(text="đoạn 4", score=0.6),
        ],
    )
    generator = FakeAnswer()
    pipeline = build_pipeline(RetrievalMode.VECTOR, context, generator)
    result = pipeline.ask(user_id="u1", conversation_id="c1", question="Hỏi")
    assert result["sources"] == ["QĐ-01", "QĐ-02"]
