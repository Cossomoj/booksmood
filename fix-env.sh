#!/bin/bash

# BooksMood - Исправление .env файла
# Исправляет проблемы с паролями содержащими недопустимые символы

set -e

PROJECT_DIR="/opt/booksmood"
ENV_FILE="$PROJECT_DIR/.env"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 BooksMood - Исправление .env файла${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
    exit 1
}

# Проверка прав sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        log "Запуск с правами sudo..."
        exec sudo "$0" "$@"
    fi
}

# Генерация безопасных паролей (только буквы и цифры)
generate_safe_password() {
    openssl rand -hex 16
}

# Проверка существования файла
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        error ".env файл не найден: $ENV_FILE"
    fi
    
    if [ ! -d "$PROJECT_DIR" ]; then
        error "Директория проекта не найдена: $PROJECT_DIR"
    fi
    
    log ".env файл найден: $ENV_FILE"
}

# Создание резервной копии
backup_env() {
    BACKUP_FILE="$PROJECT_DIR/.env.backup-$(date +%Y%m%d-%H%M%S)"
    log "Создание резервной копии: $BACKUP_FILE"
    cp "$ENV_FILE" "$BACKUP_FILE"
    log "Резервная копия создана"
}

# Исправление .env файла
fix_env_file() {
    log "Исправление .env файла..."
    
    # Генерируем новые безопасные пароли
    POSTGRES_PASSWORD=$(generate_safe_password)
    REDIS_PASSWORD=$(generate_safe_password)
    JWT_SECRET=$(generate_safe_password)$(generate_safe_password)
    SESSION_SECRET=$(generate_safe_password)
    MINIO_PASSWORD=$(generate_safe_password)
    MINIO_SECRET=$(generate_safe_password)
    
    log "Сгенерированы новые безопасные пароли"
    
    # Создаем новый .env файл
    cat > "$ENV_FILE" << EOF
# ==============================================
# TELEGRAM BOT НАСТРОЙКИ
# ==============================================
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/webhook

# ==============================================
# DATABASE НАСТРОЙКИ  
# ==============================================
POSTGRES_DB=booksmood
POSTGRES_USER=booksmood_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://booksmood_user:${POSTGRES_PASSWORD}@postgres:5432/booksmood

# ==============================================
# REDIS НАСТРОЙКИ
# ==============================================
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# ==============================================
# SECURITY НАСТРОЙКИ
# ==============================================
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRES_IN=7d
SESSION_SECRET=${SESSION_SECRET}

# ==============================================
# API НАСТРОЙКИ
# ==============================================
API_URL=http://localhost:3001
FRONTEND_URL=http://localhost:3000
ADMIN_URL=http://localhost:3002

# ==============================================
# MINIO S3 НАСТРОЙКИ
# ==============================================
MINIO_ROOT_USER=booksmood
MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
MINIO_BUCKET_NAME=audiobooks
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=booksmood
MINIO_SECRET_KEY=${MINIO_SECRET}

# ==============================================
# PRODUCTION НАСТРОЙКИ
# ==============================================
NODE_ENV=production
PORT=3001
CORS_ORIGIN=*

# ==============================================
# ADMIN PANEL НАСТРОЙКИ
# ==============================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@booksmood.com

# ==============================================
# BACKUP НАСТРОЙКИ
# ==============================================
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
EOF

    log ".env файл исправлен с новыми безопасными паролями"
}

# Перезапуск проекта
restart_project() {
    log "Перезапуск проекта с новыми настройками..."
    
    cd "$PROJECT_DIR"
    
    # Остановка контейнеров
    if command -v docker-compose &> /dev/null; then
        docker-compose down || true
        
        # Удаление volumes чтобы применить новые пароли
        warn "Удаление старых volumes с данными (будут пересозданы)..."
        docker-compose down --volumes || true
        
        # Запуск с новыми настройками
        log "Запуск контейнеров с новыми паролями..."
        docker-compose up -d --force-recreate
        
        # Ожидание запуска
        log "Ожидание запуска сервисов..."
        sleep 30
        
        # Инициализация базы данных
        log "Инициализация базы данных..."
        docker-compose exec -T backend npm run db:migrate || true
        docker-compose exec -T backend npm run db:seed || true
        
        log "Проект перезапущен успешно"
    else
        error "docker-compose не найден"
    fi
}

# Проверка статуса
check_status() {
    log "Проверка статуса контейнеров..."
    
    cd "$PROJECT_DIR"
    
    if docker-compose ps; then
        log "Статус контейнеров проверен"
    else
        warn "Ошибка при проверке статуса"
    fi
}

# Вывод итоговой информации
show_final_info() {
    echo ""
    echo -e "${GREEN}✅ .env файл успешно исправлен!${NC}"
    echo -e "${GREEN}==============================${NC}"
    echo ""
    echo -e "${BLUE}📋 Что было сделано:${NC}"
    echo "   • Создана резервная копия старого .env"
    echo "   • Сгенерированы новые безопасные пароли"
    echo "   • Перезапущены все контейнеры"
    echo "   • Пересоздана база данных"
    echo ""
    echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
    echo "   • Добавьте свой TELEGRAM_BOT_TOKEN в .env файл"
    echo "   • Резервная копия сохранена в том же каталоге"
    echo ""
    echo -e "${GREEN}🔧 Команды для управления:${NC}"
    echo "   Статус:      cd $PROJECT_DIR && docker-compose ps"
    echo "   Логи:        cd $PROJECT_DIR && docker-compose logs -f"
    echo "   Перезапуск:  cd $PROJECT_DIR && docker-compose restart"
    echo ""
}

# Главная функция
main() {
    log "Начало исправления .env файла..."
    
    check_sudo "$@"
    check_env_file
    backup_env
    fix_env_file
    restart_project
    check_status
    show_final_info
}

# Обработка параметров командной строки
case "${1:-}" in
    --help|-h)
        echo "BooksMood - Исправление .env файла"
        echo ""
        echo "Использование:"
        echo "  bash fix-env.sh          # Исправить .env файл"
        echo "  bash fix-env.sh --help   # Эта справка"
        echo ""
        echo "Скрипт исправляет проблемы с паролями в .env файле,"
        echo "которые содержат недопустимые символы (/, +, =)"
        echo ""
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 