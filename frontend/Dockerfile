# Frontend ChatBot TLU: phục vụ tệp tĩnh bằng nginx
# Build:  docker build -t chatbot-tlu-frontend .
# Chạy:   xem docker-compose.yml (khuyến nghị)

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public/ /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
