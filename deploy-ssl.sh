#!/bin/bash

# 🔐 Скрипт развертывания BooksMood с SSL на VPS
# Использование: ./deploy-ssl.sh

set -e

echo "🔐 BooksMood SSL Deployment Script"
echo "=================================="

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка DNS
echo -e "${BLUE}📡 Проверка DNS записи...${NC}"
DNS_IP=$(dig +short app.booksmood.ru)
if [ "$DNS_IP" != "213.171.25.85" ]; then
    echo -e "${RED}❌ DNS запись неверна: $DNS_IP != 213.171.25.85${NC}"
    echo -e "${YELLOW}⚠️  Обновите A-запись app.booksmood.ru на 213.171.25.85${NC}"
    exit 1
fi
echo -e "${GREEN}✅ DNS: app.booksmood.ru → $DNS_IP${NC}"

# VPS параметры
VPS_USER="user1"
VPS_HOST="213.171.25.85"
VPS_KEY="~/.ssh/id_ed25519"
PROJECT_DIR="/opt/booksmood-ssl"

echo -e "${BLUE}🖥️  Подключение к VPS: $VPS_USER@$VPS_HOST${NC}"

# Создание docker-compose.yml на VPS
echo -e "${BLUE}📝 Создание SSL конфигурации...${NC}"

ssh -i $VPS_KEY $VPS_USER@$VPS_HOST << 'EOF'
# Остановка старых контейнеров
echo "🛑 Остановка старых контейнеров..."
sudo docker-compose down 2>/dev/null || true
cd /opt/booksmood && sudo docker-compose down 2>/dev/null || true

# Создание директории проекта
sudo mkdir -p /opt/booksmood-ssl
cd /opt/booksmood-ssl

# Создание docker-compose.yml
echo "📝 Создание docker-compose.yml..."
sudo tee docker-compose.yml > /dev/null << 'COMPOSE_EOF'
services:
  booksmood:
    build:
      context: https://github.com/Cossomoj/booksmood.git
      dockerfile: Dockerfile.ssl
    container_name: booksmood_ssl_app
    ports:
      - "80:80"
      - "443:443"
      - "8000:8000"
    volumes:
      - booksmood_data:/app/data
      - booksmood_uploads:/app/app/static/uploads
      - booksmood_logs:/var/log
      - booksmood_ssl:/etc/letsencrypt
    environment:
      - BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY
      - TELEGRAM_BOT_USERNAME=booksmoodbot
      - SECRET_KEY=booksmood-ssl-secret-key-2024-CHANGE-IN-PRODUCTION
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=10080
      - DATABASE_URL=sqlite:///./data/audioflow.db
      - DEBUG=false
      - APP_NAME=BooksMood
      - HOST=0.0.0.0
      - PORT=8000
      - UPLOAD_DIR=./app/static/uploads
      - MAX_FILE_SIZE=104857600
      - CORS_ORIGINS=["https://web.telegram.org", "https://app.booksmood.ru", "http://localhost"]
      - PRODUCTION_URL=https://app.booksmood.ru
      - SSL_DOMAIN=app.booksmood.ru
      - SSL_EMAIL=admin@booksmood.ru
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    networks:
      - booksmood_network
    labels:
      - "com.booksmood.service=api-ssl"
      - "com.booksmood.version=1.0-ssl"
      - "com.booksmood.domain=app.booksmood.ru"

networks:
  booksmood_network:
    driver: bridge
    name: booksmood_ssl_net

volumes:
  booksmood_data:
    name: booksmood_ssl_database
    driver: local
  booksmood_uploads:
    name: booksmood_ssl_files
    driver: local
  booksmood_logs:
    name: booksmood_ssl_logs
    driver: local
  booksmood_ssl:
    name: booksmood_ssl_certs
    driver: local
COMPOSE_EOF

echo "✅ Конфигурация создана"
EOF

# Запуск контейнера
echo -e "${BLUE}🚀 Запуск SSL контейнера...${NC}"
ssh -i $VPS_KEY $VPS_USER@$VPS_HOST << 'EOF'
cd /opt/booksmood-ssl

echo "🔄 Сборка и запуск контейнера..."
sudo docker-compose up --build -d

echo "⏳ Ожидание инициализации (2 минуты)..."
sleep 120

echo "📊 Статус контейнера:"
sudo docker-compose ps

echo "📋 Логи SSL setup:"
sudo docker-compose logs booksmood | grep -A 10 -B 5 "SSL\|ssl\|certificate\|cert" || echo "SSL логи пока недоступны"
EOF

# Проверка результата
echo -e "${BLUE}🧪 Проверка результата...${NC}"
echo "⏳ Ожидание 30 секунд для завершения настройки..."
sleep 30

echo -e "${BLUE}🌐 Тестирование доступности:${NC}"

# Тест HTTP
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://app.booksmood.ru/health --connect-timeout 10 || echo "ERROR")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ HTTP: app.booksmood.ru работает${NC}"
elif [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "${GREEN}✅ HTTP: Редирект на HTTPS (ожидаемо)${NC}"
else
    echo -e "${RED}❌ HTTP: Статус $HTTP_STATUS${NC}"
fi

# Тест HTTPS
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.booksmood.ru/health --connect-timeout 15 -k || echo "ERROR")
if [ "$HTTPS_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS: app.booksmood.ru работает${NC}"
    echo -e "${GREEN}🎉 Успешно! Доступно по https://app.booksmood.ru${NC}"
    
    # Тест API
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.booksmood.ru:8000/docs --connect-timeout 10 -k || echo "ERROR")
    if [ "$API_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ API Docs: https://app.booksmood.ru:8000/docs${NC}"
    fi
    
else
    echo -e "${YELLOW}⚠️  HTTPS: Статус $HTTPS_STATUS (возможно сертификат еще настраивается)${NC}"
    echo -e "${BLUE}ℹ️  Попробуйте через 5-10 минут: https://app.booksmood.ru${NC}"
fi

echo ""
echo -e "${GREEN}🔗 Полезные ссылки:${NC}"
echo -e "${BLUE}📱 Сайт:     https://app.booksmood.ru${NC}"
echo -e "${BLUE}📚 API Docs: https://app.booksmood.ru:8000/docs${NC}"
echo -e "${BLUE}👤 Админ:    https://app.booksmood.ru/admin/login${NC}"
echo -e "${BLUE}🔐 Логин:    admin / admin123${NC}"

echo ""
echo -e "${YELLOW}📋 Команды для мониторинга:${NC}"
echo "ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 'cd /opt/booksmood-ssl && sudo docker-compose logs -f'"
echo "ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 'sudo docker-compose ps'"

echo -e "${GREEN}✅ Развертывание завершено!${NC}" 