#!/bin/bash

# 🧪 Тестирование Docker развертывания BooksMood
# ===============================================

set -e

echo "🧪 Тестирование Docker развертывания BooksMood"
echo "================================================"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 установлен${NC}"
    else
        echo -e "${RED}❌ $1 не найден${NC}"
        exit 1
    fi
}

test_endpoint() {
    local url=$1
    local name=$2
    
    echo -e "${BLUE}🔍 Тестирование $name: $url${NC}"
    
    if curl -s --max-time 10 "$url" > /dev/null; then
        echo -e "${GREEN}✅ $name доступен${NC}"
    else
        echo -e "${RED}❌ $name недоступен${NC}"
        return 1
    fi
}

# Проверка предварительных требований
echo -e "${BLUE}📋 Проверка требований...${NC}"
check_command "docker"
check_command "docker-compose"

# Проверка версий
echo -e "${BLUE}ℹ️ Версии:${NC}"
docker --version
docker-compose --version

# Остановка существующих контейнеров
echo -e "${YELLOW}⏹️ Остановка существующих контейнеров...${NC}"
docker-compose down 2>/dev/null || true

# Запуск с одной командой
echo -e "${GREEN}🚀 Запуск BooksMood одной командой...${NC}"
sudo docker-compose up --build -d

# Ожидание запуска
echo -e "${YELLOW}⏳ Ожидание запуска сервисов (60 секунд)...${NC}"
sleep 60

# Проверка статуса контейнеров
echo -e "${BLUE}📊 Статус контейнеров:${NC}"
docker-compose ps

# Тестирование endpoint'ов
echo -e "${BLUE}🔍 Тестирование endpoint'ов...${NC}"

# Основные endpoint'ы
test_endpoint "http://localhost/health" "Health Check"
test_endpoint "http://localhost:8000/health" "API Health"
test_endpoint "http://localhost/" "Главная страница"
test_endpoint "http://localhost:8000/docs" "API Документация"
test_endpoint "http://localhost/admin/login" "Админ панель"

# Проверка API
echo -e "${BLUE}🔍 Тестирование API...${NC}"
api_response=$(curl -s http://localhost:8000/health)
if [[ $api_response == *"AudioFlow API"* ]]; then
    echo -e "${GREEN}✅ API отвечает корректно${NC}"
else
    echo -e "${RED}❌ Некорректный ответ API: $api_response${NC}"
fi

# Проверка базы данных
echo -e "${BLUE}🗄️ Проверка базы данных...${NC}"
if docker exec booksmood_app sqlite3 /app/audioflow.db "SELECT COUNT(*) FROM categories;" > /dev/null 2>&1; then
    categories_count=$(docker exec booksmood_app sqlite3 /app/audioflow.db "SELECT COUNT(*) FROM categories;")
    echo -e "${GREEN}✅ База данных работает, категорий: $categories_count${NC}"
else
    echo -e "${RED}❌ Проблема с базой данных${NC}"
fi

# Проверка логов на ошибки
echo -e "${BLUE}📋 Проверка логов на ошибки...${NC}"
if docker-compose logs | grep -i "error\|exception\|failed" | head -5; then
    echo -e "${YELLOW}⚠️ Найдены ошибки в логах (см. выше)${NC}"
else
    echo -e "${GREEN}✅ Критических ошибок в логах не найдено${NC}"
fi

# Итоговый отчет
echo ""
echo -e "${GREEN}🎉 Тестирование завершено!${NC}"
echo "================================================"
echo -e "🌐 Сайт: ${BLUE}http://localhost${NC}"
echo -e "📚 API: ${BLUE}http://localhost:8000${NC}"
echo -e "⚙️ Админ: ${BLUE}http://localhost/admin/login${NC}"
echo -e "📖 Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "👤 Админ: ${YELLOW}admin / admin123${NC}"
echo ""
echo -e "${GREEN}✅ BooksMood успешно развернут одной командой!${NC}" 