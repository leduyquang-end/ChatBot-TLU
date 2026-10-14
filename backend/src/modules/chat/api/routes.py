from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request

from src.modules.chat.application.chat_pipeline import ChatPipeline
from src.modules.chat.infrastructure.chroma_retrieval import ChromaVectorRetrieval
from src.modules.chat.infrastructure.hf_embedder import SentenceTransformerEmbedder
from src.modules.chat.infrastructure.memory_conversation_store import (
    InMemoryConversationStore,
)
from src.modules.chat.infrastructure.neo4j_graph_retrieval import Neo4jGraphRetrieval
from src.modules.chat.infrastructure.groq_router_client import GroqRouterClient
from src.modules.chat.infrastructure.qwen_answer_client import QwenAnswerClient
from src.platform.security.auth import sanitize_input, verify_token
from src.shared.common.errors import UnauthorizedError, ValidationError
from src.shared.config.settings import get_settings

bp = Blueprint("chat", __name__, url_prefix="/chat")

_conversation_store = InMemoryConversationStore()


def _require_user() -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError("Cần đăng nhập để đặt câu hỏi")
    return verify_token(auth.removeprefix("Bearer ").strip())


def _build_pipeline() -> ChatPipeline:
    settings = get_settings()
    embedder = SentenceTransformerEmbedder(settings)
    return ChatPipeline(
        router=GroqRouterClient(settings),
        vector_retrieval=ChromaVectorRetrieval(settings, embedder),
        graph_retrieval=Neo4jGraphRetrieval(settings, embedder, settings.groq_api_key),
        answer_generator=QwenAnswerClient(settings),
        conversation_store=_conversation_store,
        settings=settings,
    )


@bp.post("/ask")
def ask():
    user_id = _require_user()
    settings = get_settings()
    data = request.get_json(silent=True) or {}
    raw_question = (data.get("question") or "").strip()
    question = sanitize_input(raw_question, max_length=settings.question_max_length)
    if not question or not any(ch.isalnum() for ch in question):
        raise ValidationError("Câu hỏi không được để trống hoặc chỉ có ký tự đặc biệt")

    conversation_id = (data.get("conversation_id") or "").strip() or str(uuid.uuid4())

    pipeline = _build_pipeline()
    result = pipeline.ask(
        user_id=user_id, conversation_id=conversation_id, question=question
    )
    return jsonify(result)


@bp.get("/history")
def history():
    user_id = _require_user()
    conversation_id = request.args.get("conversation_id", "").strip()
    if not conversation_id:
        raise ValidationError("Thiếu conversation_id")
    pipeline = _build_pipeline()
    turns = pipeline.history(user_id=user_id, conversation_id=conversation_id)
    return jsonify({"conversation_id": conversation_id, "turns": turns})
