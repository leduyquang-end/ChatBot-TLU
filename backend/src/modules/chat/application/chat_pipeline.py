from __future__ import annotations

import logging

from src.modules.chat.application.ports.answer_generator import AnswerGeneratorPort
from src.modules.chat.application.ports.conversation_store import ConversationStorePort
from src.modules.chat.application.ports.retrieval import (
    GraphRetrievalPort,
    VectorRetrievalPort,
)
from src.modules.chat.application.ports.router import RouterPort
from src.modules.chat.domain.no_info import NoInfoPolicy
from src.modules.chat.domain.prompt import NO_INFO_MESSAGE, build_prompt
from src.modules.chat.domain.retrieval_mode import RetrievalMode
from src.modules.chat.domain.retrieval_result import (
    GraphContext,
    RetrievedChunk,
    RetrievedContext,
)
from src.shared.common.errors import ExternalServiceError
from src.shared.config.settings import Settings

logger = logging.getLogger(__name__)


class ChatPipeline:
    """Điều phối luồng hỏi đáp QT-01 (AGENTS mục 5.1)."""

    def __init__(
        self,
        *,
        router: RouterPort,
        vector_retrieval: VectorRetrievalPort,
        graph_retrieval: GraphRetrievalPort,
        answer_generator: AnswerGeneratorPort,
        conversation_store: ConversationStorePort,
        settings: Settings,
    ) -> None:
        self._router = router
        self._vector_retrieval = vector_retrieval
        self._graph_retrieval = graph_retrieval
        self._answer_generator = answer_generator
        self._conversation_store = conversation_store
        self._settings = settings
        self._no_info = NoInfoPolicy(settings.no_info_threshold)

    def ask(self, *, user_id: str, conversation_id: str, question: str) -> dict:
        conversation = self._conversation_store.get_or_create(conversation_id, user_id)
        history = conversation.history(self._settings.history_max_turns)

        mode = self._router.classify(question)
        logger.info("event=chat.router.selected mode=%s", mode.value)

        context = self._retrieve(question, mode)

        # QT-01: "Không cần tìm" (lời chào) vẫn soạn câu trả lời với ngữ cảnh
        # rỗng — không rơi vào thông báo "chưa có thông tin".
        if mode != RetrievalMode.NONE and not self._no_info.has_relevant_info(context):
            logger.info("event=chat.no_info mode=%s", mode.value)
            answer = NO_INFO_MESSAGE
        else:
            prompt = build_prompt(question, context, history)
            answer = self._answer_generator.generate(prompt)

        conversation.add_turn(question, answer)
        self._conversation_store.save(conversation)

        return {
            "answer": answer,
            "mode": mode.value,
            "conversation_id": conversation.conversation_id,
            # bỏ trùng: nhiều đoạn cùng nguồn chỉ liệt kê một lần
            "sources": list(
                dict.fromkeys(
                    c.citation() for c in context.chunks if c.citation()
                )
            ),
        }

    def history(self, *, user_id: str, conversation_id: str) -> list[dict]:
        conversation = self._conversation_store.get_or_create(conversation_id, user_id)
        if conversation.user_id != user_id:
            return []
        return conversation.turns

    def _retrieve(self, question: str, mode: RetrievalMode) -> RetrievedContext:
        if mode == RetrievalMode.NONE:
            return RetrievedContext(mode=mode.value)

        s = self._settings
        chunks: list[RetrievedChunk] = []
        graph = GraphContext()

        if mode in (RetrievalMode.VECTOR, RetrievalMode.HYBRID):
            ctx = self._vector_retrieval.retrieve(
                question, fetch_k=s.fetch_k, top_k=s.top_k
            )
            chunks.extend(ctx.chunks)

        if mode in (RetrievalMode.GRAPH, RetrievalMode.HYBRID):
            try:
                ctx = self._graph_retrieval.retrieve(
                    question, alpha=s.alpha, fetch_k=s.fetch_k
                )
                if ctx.graph.nodes or ctx.graph.edges:
                    graph = ctx.graph
                chunks.extend(ctx.chunks)
            except ExternalServiceError:
                # Mục 7.2: Neo4j lỗi → chỉ dùng Vector, người dùng không thấy lỗi
                logger.error(
                    "event=chat.retrieval.graph.unavailable mode=%s", mode.value
                )
                if mode == RetrievalMode.GRAPH:
                    ctx = self._vector_retrieval.retrieve(
                        question, fetch_k=s.fetch_k, top_k=s.top_k
                    )
                    chunks.extend(ctx.chunks)

        return RetrievedContext(mode=mode.value, chunks=chunks, graph=graph)
