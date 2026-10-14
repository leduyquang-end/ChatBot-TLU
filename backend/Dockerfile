# syntax=docker/dockerfile:1
#
# Dockerfile cho ứng dụng ChatBot TLU.
# Giả định: ứng dụng viết bằng Python, dùng Flask, có file requirements.txt ở gốc.
# Nếu khác, chỉnh các mục đánh dấu [Điền].
#
# Build:  docker build -t chatbot-tlu:latest .
# Chạy:   xem docker-compose.yml (khuyến nghị)

# ---------------------------------------------------------------
# Giai đoạn 1: cài phụ thuộc vào một thư mục riêng
# ---------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Các thư viện biên dịch cần thiết cho một số gói (nếu có). Xóa nếu không cần.
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Cài torch bản CPU để image nhỏ hơn và chạy được trên mọi máy không có GPU.
# Bỏ dòng này nếu không dùng sentence-transformers hay torch.
RUN pip install --prefix=/install --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --prefix=/install -r requirements.txt

# ---------------------------------------------------------------
# Giai đoạn 2: image chạy thật
# ---------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    HF_HOME=/home/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/app/.cache/huggingface

# Người dùng không phải root để chạy ứng dụng
RUN groupadd --system app \
 && useradd --system --gid app --home-dir /home/app --create-home app

WORKDIR ${APP_HOME}

# Phụ thuộc đã cài ở giai đoạn trước
COPY --from=builder /install /usr/local

# Mã nguồn
COPY src/ ./src/
COPY scripts/ ./scripts/

# Thư mục ghi được cho cache mô hình và log
RUN mkdir -p /home/app/.cache/huggingface /app/logs \
 && chown -R app:app /home/app /app

USER app

EXPOSE 8000

# Kiểm tra sức khỏe. Cần có endpoint /health trong ứng dụng [Điền: đường dẫn thật].
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

# Chạy bằng gunicorn, không dùng server phát triển của Flask.
# [Điền: module:biến Flask thật, ví dụ src.main:app hoặc src.modules.chat.api:app]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "src.main:app"]