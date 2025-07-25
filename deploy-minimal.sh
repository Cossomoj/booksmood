#!/bin/bash

# 🚀 Минимальное развертывание BooksMood на VPS
# =============================================

set -e

echo "🚀 Развертывание BooksMood на VPS"
echo "================================="

# Создание docker-compose.yml на VPS
cat > docker-compose.yml << 'EOF'
services:
  # BooksMood основное приложение
  booksmood:
    build:
      context: https://github.com/Cossomoj/booksmood.git
      dockerfile: Dockerfile
    container_name: booksmood_app
    ports:
      - "80:80"      # Nginx
      - "8000:8000"  # FastAPI (для прямого доступа)
    volumes:
      # Постоянное хранение базы данных
      - booksmood_data:/app/audioflow.db
      # Постоянное хранение загруженных файлов
      - booksmood_uploads:/app/app/static/uploads
      # Логи
      - booksmood_logs:/var/log
    environment:
      # Telegram Bot
      - BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY
      - TELEGRAM_BOT_USERNAME=booksmoodbot
      
      # Security
      - SECRET_KEY=booksmood-production-secret-key-2024-CHANGE-THIS
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=10080
      
      # Database
      - DATABASE_URL=sqlite:///./audioflow.db
      
      # App Settings
      - DEBUG=false
      - APP_NAME=BooksMood
      - HOST=0.0.0.0
      - PORT=8000
      
      # File Storage
      - UPLOAD_DIR=./app/static/uploads
      - MAX_FILE_SIZE=104857600
      
      # CORS Origins
      - CORS_ORIGINS=["https://web.telegram.org", "https://app.booksmood.ru", "http://213.171.25.85"]
      
      # Production
      - PRODUCTION_URL=https://app.booksmood.ru
      
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - booksmood_network
    labels:
      - "com.booksmood.service=api"
      - "com.booksmood.version=1.0"

# Сети
networks:
  booksmood_network:
    driver: bridge
    name: booksmood_net

# Тома для постоянного хранения
volumes:
  booksmood_data:
    name: booksmood_database
    driver: local
  booksmood_uploads:
    name: booksmood_files
    driver: local
  booksmood_logs:
    name: booksmood_logs
    driver: local
EOF

echo "✅ docker-compose.yml создан"

# Запуск
echo "🚀 Запуск BooksMood..."
sudo docker-compose up --build -d

echo ""
echo "🎉 BooksMood развернут!"
echo "========================"
echo "🌐 HTTP: http://213.171.25.85"
echo "📚 API: http://213.171.25.85:8000"
echo "⚙️ Админ: http://213.171.25.85/admin/login"
echo "👤 Логин: admin / admin123" 