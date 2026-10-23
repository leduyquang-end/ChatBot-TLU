# syntax=docker/dockerfile:1
#
# Dockerfile cho backend ChatBot TLU (Flask + gunicorn).
# Build:  docker build -t chatbot-tlu:latest ./backend
# Chạy:   docker compose up -d --build (khuyến nghị, kèm frontend/Chroma/Neo4j)

# ---------------------------------------------------------------
# Giai đoạn 1: cài phụ thuộc vào venv riêng (torch bản CPU)
# ---------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Cài torch CPU trước trong cùng venv: pip sẽ coi là "đã có" khi cài
# sentence-transformers, tránh tải lại bản CUDA (image nhỏ hơn nhiều).
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && /opt/venv/bin/pip install -r requirements.txt

# ---------------------------------------------------------------
# Giai đoạn 2: image chạy thật (không chứa công cụ build)
# ---------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    HF_HOME=/home/app/.cache/huggingface \
    PATH="/opt/venv/bin:$PATH"

# libgomp1 là thư viện OpenMP mà torch CPU cần lúc chạy
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system app \
 && useradd --system --gid app --home-dir /home/app --create-home app

WORKDIR ${APP_HOME}

COPY --from=builder /opt/venv /opt/venv

COPY src/ ./src/
COPY scripts/ ./scripts/

RUN mkdir -p /home/app/.cache/huggingface /app/logs \
 && chown -R app:app /home/app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

# Một worker + nhiều thread: kho phiên refresh, user và lịch sử hội thoại đang
# lưu trong RAM của từng tiến trình. Tăng worker sẽ làm mất phiên giữa các request;
# chỉ tăng sau khi chuyển các kho này sang Redis/DB dùng chung.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "300", "--graceful-timeout", "30", "src.main:app"]
