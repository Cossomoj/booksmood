FROM python:3.13-slim

# Метаданные
LABEL maintainer="BooksMood Team"
LABEL description="BooksMood AudioFlow - Telegram Mini App для аудиокниг (Manual SSL)"

# Устанавливаем системные зависимости (убираем certbot)
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    supervisor \
    nginx \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Создаём .ssh директорию и устанавливаем права
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Добавляем GitHub в known_hosts
RUN ssh-keyscan -H github.com >> /root/.ssh/known_hosts

# Клонируем репозиторий BooksMood из ветки main
RUN git clone -b main https://github.com/Cossomoj/booksmood.git . && \
    ls -la requirements.txt

# Создаём виртуальное окружение
RUN python3.13 -m venv /venv

# Устанавливаем переменные окружения
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"
ENV PYTHONPATH="/app"

# Обновляем pip и устанавливаем зависимости
RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Создаём необходимые директории
RUN mkdir -p /app/app/static/uploads
RUN mkdir -p /app/data
RUN mkdir -p /var/log
RUN mkdir -p /var/www/html
RUN mkdir -p /etc/nginx/ssl

# Устанавливаем права
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true
RUN chmod 755 /app/app/static/uploads
RUN chmod 755 /app/data

# Создаём базовую конфигурацию Nginx
RUN echo 'server {\n\
    listen 80;\n\
    server_name app.booksmood.ru;\n\
    \n\
    # Для получения SSL сертификата\n\
    location /.well-known/acme-challenge/ {\n\
        root /var/www/html;\n\
    }\n\
    \n\
    # Редирект на HTTPS если сертификат есть\n\
    location / {\n\
        if (-f /etc/nginx/ssl/fullchain.pem) {\n\
            return 301 https://$server_name$request_uri;\n\
        }\n\
        proxy_pass http://localhost:8000;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
    \n\
    location /static/ {\n\
        alias /app/app/static/;\n\
        expires 30d;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
    \n\
    location /health {\n\
        access_log off;\n\
        return 200 "healthy\\n";\n\
        add_header Content-Type text/plain;\n\
    }\n\
}\n\
\n\
# HTTPS сервер (будет работать только если есть сертификаты)\n\
server {\n\
    listen 443 ssl http2;\n\
    server_name app.booksmood.ru;\n\
    \n\
    # SSL сертификаты (будут подмонтированы из хоста)\n\
    ssl_certificate /etc/nginx/ssl/fullchain.pem;\n\
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;\n\
    \n\
    # SSL настройки\n\
    ssl_protocols TLSv1.2 TLSv1.3;\n\
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;\n\
    ssl_prefer_server_ciphers off;\n\
    ssl_session_cache shared:SSL:10m;\n\
    ssl_session_timeout 1d;\n\
    \n\
    # Security headers\n\
    add_header Strict-Transport-Security "max-age=31536000" always;\n\
    add_header X-Frame-Options DENY;\n\
    add_header X-Content-Type-Options nosniff;\n\
    \n\
    location / {\n\
        proxy_pass http://localhost:8000;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto https;\n\
    }\n\
    \n\
    location /static/ {\n\
        alias /app/app/static/;\n\
        expires 30d;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
    \n\
    location /health {\n\
        access_log off;\n\
        return 200 "healthy\\n";\n\
        add_header Content-Type text/plain;\n\
    }\n\
}\n\
\n\
# Админ панель на порту 8088\n\
server {\n\
    listen 8088;\n\
    server_name _;\n\
    \n\
    location / {\n\
        proxy_pass http://localhost:8000;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
    \n\
    location /static/ {\n\
        alias /app/app/static/;\n\
        expires 30d;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
}' > /etc/nginx/sites-available/default

# Скрипт для проверки и копирования SSL сертификатов
RUN echo '#!/bin/bash\n\
echo "🔐 Проверка SSL сертификатов..."\n\
\n\
if [ -f "/host-ssl/fullchain.pem" ] && [ -f "/host-ssl/privkey.pem" ]; then\n\
    echo "✅ SSL сертификаты найдены, копируем..."\n\
    cp /host-ssl/*.pem /etc/nginx/ssl/ 2>/dev/null || true\n\
    chmod 644 /etc/nginx/ssl/*.pem\n\
    echo "✅ SSL сертификаты скопированы"\n\
    echo "🔐 HTTPS будет доступен по адресу: https://app.booksmood.ru"\n\
else\n\
    echo "⚠️  SSL сертификаты не найдены в /host-ssl/"\n\
    echo "🔧 Работаем только по HTTP: http://app.booksmood.ru"\n\
    echo "💡 Для генерации сертификата запустите на VPS:"\n\
    echo "   bash /opt/ssl-certs/ssl-generate.sh"\n\
fi\n\
' > /app/check-ssl.sh && chmod +x /app/check-ssl.sh

# Инициализация базы данных при сборке
RUN cd /app && /venv/bin/python scripts/init_db.py

# Создаём конфигурацию supervisor
RUN echo '[supervisord]\n\
nodaemon=true\n\
logfile=/var/log/supervisord.log\n\
logfile_maxbytes=50MB\n\
logfile_backups=10\n\
loglevel=info\n\
\n\
[program:ssl_check]\n\
command=/app/check-ssl.sh\n\
autostart=true\n\
autorestart=false\n\
stdout_logfile=/var/log/ssl_check.log\n\
stderr_logfile=/var/log/ssl_check_err.log\n\
priority=50\n\
startsecs=0\n\
exitcodes=0,1,2\n\
\n\
[program:nginx]\n\
command=/usr/sbin/nginx -g "daemon off;"\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/nginx.log\n\
stderr_logfile=/var/log/nginx_err.log\n\
priority=100\n\
\n\
[program:booksmood_api]\n\
command=/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/booksmood_api.log\n\
stderr_logfile=/var/log/booksmood_api_err.log\n\
environment=PYTHONPATH="/app"\n\
user=root\n\
priority=200\n\
startretries=5\n\
stopasgroup=true\n\
killasgroup=true\n\
' > /etc/supervisor/conf.d/booksmood.conf

# Копируем environment файл по умолчанию
RUN echo '# BooksMood Docker Environment (Manual SSL)\n\
BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY\n\
TELEGRAM_BOT_USERNAME=booksmoodbot\n\
SECRET_KEY=booksmood-docker-secret-key-2024-change-in-production\n\
ALGORITHM=HS256\n\
ACCESS_TOKEN_EXPIRE_MINUTES=10080\n\
DATABASE_URL=sqlite:///./data/audioflow.db\n\
DEBUG=False\n\
APP_NAME=BooksMood\n\
UPLOAD_DIR=./app/static/uploads\n\
MAX_FILE_SIZE=104857600\n\
HOST=0.0.0.0\n\
PORT=8000\n\
PRODUCTION_URL=https://app.booksmood.ru\n\
' > /app/.env

# Открываем порты
EXPOSE 80 443 8000 8088

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Запускаем supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/booksmood.conf"] 