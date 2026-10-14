from src.modules.chat.application.chat_pipeline import ChatPipeline
from src.modules.chat.domain.conversation import Conversation
from src.modules.chat.domain.retrieval_mode import RetrievalMode
from src.modules.chat.domain.retrieval_result import (
    RetrievedChunk,
    RetrievedContext,
)
from src.shared.config.settings import Settings


def make_settings(**overrides) -> Settings:
    base = dict(
        groq_api_key="g",
        qwen_api_key="q",
        hf_token="h",
        chroma_url="http://localhost:8000",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="pw",
        no_info_threshold=0.15,
    )
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


def build_pipeline(mode: RetrievalMode, context: RetrievedContext, generator: FakeAnswer):
    return ChatPipeline(
        router=FakeRouter(mode),
        vector_retrieval=FakeVector(context),
        graph_retrieval=FakeGraph(),
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
