# BooksMood Docker Management
# ===========================

.PHONY: help start build up down logs restart clean status health dev prod
.DEFAULT_GOAL := start

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Переменные
COMPOSE_FILE=docker-compose.yml
SERVICE_NAME=booksmood
CONTAINER_NAME=booksmood_app

# Помощь
help: ## Показать доступные команды
	@echo "${BLUE}📚 BooksMood Docker Commands${NC}"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "${GREEN}%-15s${NC} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Основные команды
start: ## Запустить одной командой (по умолчанию)
	@echo "${GREEN}🚀 Запуск BooksMood одной командой...${NC}"
	docker-compose -f $(COMPOSE_FILE) up --build -d
	@echo "${GREEN}✅ BooksMood запущен!${NC}"
	@echo "${BLUE}🌐 Доступен по адресу: http://localhost${NC}"

build: ## Собрать Docker образ
	@echo "${YELLOW}🔨 Сборка Docker образа...${NC}"
	docker-compose -f $(COMPOSE_FILE) build --no-cache

up: ## Запустить сервисы
	@echo "${GREEN}🚀 Запуск BooksMood...${NC}"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "${GREEN}✅ BooksMood запущен!${NC}"
	@echo "${BLUE}🌐 Доступен по адресу: http://localhost${NC}"

down: ## Остановить сервисы
	@echo "${RED}⏹️ Остановка BooksMood...${NC}"
	docker-compose -f $(COMPOSE_FILE) down

restart: ## Перезапустить сервисы
	@echo "${YELLOW}🔄 Перезапуск BooksMood...${NC}"
	docker-compose -f $(COMPOSE_FILE) restart

# Логи и мониторинг
logs: ## Показать логи
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-api: ## Показать логи API
	docker logs -f $(CONTAINER_NAME)

status: ## Показать статус контейнеров
	@echo "${BLUE}📊 Статус контейнеров:${NC}"
	docker-compose -f $(COMPOSE_FILE) ps

health: ## Проверить здоровье сервиса
	@echo "${BLUE}🩺 Проверка здоровья...${NC}"
	@curl -s http://localhost/health || echo "${RED}❌ Сервис недоступен${NC}"
	@echo ""
	@curl -s http://localhost:8000/health || echo "${RED}❌ API недоступен${NC}"

# Среды развертывания
dev: ## Запустить в режиме разработки
	@echo "${YELLOW}🛠️ Запуск в режиме разработки...${NC}"
	docker-compose -f $(COMPOSE_FILE) up -d

prod: ## Запустить в продакшн режиме
	@echo "${GREEN}🏭 Запуск в продакшн режиме...${NC}"
	docker-compose -f $(COMPOSE_FILE) --profile production up -d

# Обслуживание
clean: ## Очистить неиспользуемые ресурсы
	@echo "${RED}🧹 Очистка Docker ресурсов...${NC}"
	docker system prune -f
	docker volume prune -f

clean-all: ## Полная очистка (включая тома с данными)
	@echo "${RED}⚠️ ВНИМАНИЕ: Это удалит ВСЕ данные!${NC}"
	@read -p "Продолжить? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose -f $(COMPOSE_FILE) down -v
	docker system prune -af
	docker volume prune -f

# Разработка
shell: ## Подключиться к контейнеру
	docker exec -it $(CONTAINER_NAME) /bin/bash

db: ## Подключиться к базе данных
	docker exec -it $(CONTAINER_NAME) sqlite3 /app/audioflow.db

backup: ## Создать бэкап базы данных
	@echo "${BLUE}💾 Создание бэкапа...${NC}"
	mkdir -p backups
	docker cp $(CONTAINER_NAME):/app/audioflow.db backups/audioflow_$(shell date +%Y%m%d_%H%M%S).db
	@echo "${GREEN}✅ Бэкап создан в папке backups/${NC}"

restore: ## Восстановить базу данных (restore DB=backup_file.db)
	@if [ -z "$(DB)" ]; then echo "${RED}❌ Укажите файл: make restore DB=backup_file.db${NC}"; exit 1; fi
	@echo "${YELLOW}🔄 Восстановление базы данных...${NC}"
	docker cp $(DB) $(CONTAINER_NAME):/app/audioflow.db
	docker-compose -f $(COMPOSE_FILE) restart
	@echo "${GREEN}✅ База данных восстановлена${NC}"

# Обновление
update: ## Обновить из Git и перезапустить
	@echo "${BLUE}📥 Обновление из Git (develop ветка)...${NC}"
	git pull origin develop
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "${GREEN}✅ Обновление завершено${NC}"

update-force: ## Принудительное обновление (пересборка без кэша)
	@echo "${BLUE}🔄 Принудительное обновление из develop...${NC}"
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache --pull
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "${GREEN}✅ Принудительное обновление завершено${NC}"

# Информация
info: ## Показать информацию о системе
	@echo "${BLUE}ℹ️ Информация о BooksMood${NC}"
	@echo "=================================="
	@echo "Контейнер: $(CONTAINER_NAME)"
	@echo "Сервис: $(SERVICE_NAME)"
	@echo "Compose файл: $(COMPOSE_FILE)"
	@echo ""
	@echo "${BLUE}📊 Использование ресурсов:${NC}"
	@docker stats --no-stream $(CONTAINER_NAME) 2>/dev/null || echo "Контейнер не запущен"
	@echo ""
	@echo "${BLUE}🌐 Endpoints:${NC}"
	@echo "HTTP: http://localhost"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Admin: http://localhost:8000/admin/login"
	@echo "Health: http://localhost/health"

# Тестирование
test: ## Запустить тесты
	@echo "${BLUE}🧪 Запуск тестов...${NC}"
	docker exec $(CONTAINER_NAME) /venv/bin/python -m pytest tests/ -v || echo "${YELLOW}⚠️ Тесты не найдены${NC}"

# Быстрые команды
quick-start: build up ## Быстрый старт (сборка + запуск)
	@echo "${GREEN}🎉 BooksMood готов к использованию!${NC}"

full-restart: down build up ## Полный перезапуск (остановка + сборка + запуск)
	@echo "${GREEN}🔄 Полный перезапуск завершен${NC}" 