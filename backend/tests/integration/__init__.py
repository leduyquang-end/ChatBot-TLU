"""Test tích hợp infrastructure — chạy THẬT trên dịch vụ đang mở.

Chạy: pytest tests/integration -q
- Chroma :8001 / Neo4j :7687 / Groq không mở hoặc thiếu key → test tương ứng SKIP.
- Cần môi trường như bình thường (venv backend, HF_HOME trỏ E:\\hf_cache).
"""
