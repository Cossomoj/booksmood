FROM python:3.13-slim

# Метаданные
LABEL maintainer="BooksMood Team"
LABEL description="BooksMood AudioFlow - Telegram Mini App для аудиокниг"

# Устанавливаем системные зависимости
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

# Клонируем репозиторий BooksMood напрямую в /app
RUN git clone https://github.com/Cossomoj/booksmood.git . && \
    ls -la && \
    test -f requirements.txt

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
RUN mkdir -p /var/log
RUN mkdir -p /var/www/html

# Устанавливаем права
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true
RUN chmod 755 /app/app/static/uploads

# Создаём конфигурацию Nginx
RUN echo 'server {\n\
    listen 80;\n\
    server_name localhost;\n\
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
    \n\
    location /health {\n\
        access_log off;\n\
        return 200 "healthy\\n";\n\
        add_header Content-Type text/plain;\n\
    }\n\
}' > /etc/nginx/sites-available/default

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
RUN echo '# BooksMood Docker Environment\n\
BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY\n\
TELEGRAM_BOT_USERNAME=booksmoodbot\n\
SECRET_KEY=booksmood-docker-secret-key-2024-change-in-production\n\
ALGORITHM=HS256\n\
ACCESS_TOKEN_EXPIRE_MINUTES=10080\n\
DATABASE_URL=sqlite:///./audioflow.db\n\
DEBUG=False\n\
APP_NAME=BooksMood\n\
UPLOAD_DIR=./app/static/uploads\n\
MAX_FILE_SIZE=104857600\n\
HOST=0.0.0.0\n\
PORT=8000\n\
' > /app/.env

# Открываем порты
EXPOSE 80 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Запускаем supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/booksmood.conf"] 