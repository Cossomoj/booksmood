#!/bin/bash

# BooksMood Server Deployment Script
# Для запуска на сервере user1@213.171.25.85

set -e

# Конфигурация сервера
SERVER_USER="user1"
SERVER_HOST="213.171.25.85"
SSH_KEY="~/.ssh/id_ed25519"
REPO_URL="git@github.com:Cossomoj/booksmood.git"
DEPLOY_DIR="/opt/booksmood"
PROJECT_NAME="booksmood"

echo "🚀 BooksMood Server Deployment"
echo "==============================="
echo "🌐 Сервер: $SERVER_USER@$SERVER_HOST"
echo "📁 Директория: $DEPLOY_DIR"
echo "📦 Репозиторий: $REPO_URL"
echo ""

# Функция для выполнения команд на сервере
run_on_server() {
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "$1"
}

# Функция для копирования файлов на сервер
copy_to_server() {
    scp -i "$SSH_KEY" "$1" "$SERVER_USER@$SERVER_HOST:$2"
}

# Проверка доступности сервера
check_server() {
    echo "🔍 Проверка доступности сервера..."
    
    if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo 'Сервер доступен'" > /dev/null 2>&1; then
        echo "❌ Не удается подключиться к серверу $SERVER_HOST"
        echo "Проверьте:"
        echo "  - SSH ключ: $SSH_KEY"
        echo "  - Доступность сервера"
        echo "  - Права доступа"
        exit 1
    fi
    
    echo "✅ Сервер доступен"
}

# Подготовка сервера
prepare_server() {
    echo "📋 Подготовка сервера..."
    
    run_on_server "
        # Обновление пакетов
        sudo apt update -qq
        
        # Установка Docker если не установлен
        if ! command -v docker &> /dev/null; then
            echo '🐳 Установка Docker...'
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        fi
        
        # Установка Docker Compose если не установлен
        if ! command -v docker-compose &> /dev/null; then
            echo '🔧 Установка Docker Compose...'
            sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
        
        # Установка Git если не установлен
        if ! command -v git &> /dev/null; then
            echo '📥 Установка Git...'
            sudo apt install -y git
        fi
        
        # Создание директории проекта
        sudo mkdir -p $DEPLOY_DIR
        sudo chown $USER:$USER $DEPLOY_DIR
        
        echo '✅ Сервер подготовлен'
    "
}

# Клонирование или обновление репозитория
update_repository() {
    echo "📦 Обновление репозитория..."
    
    run_on_server "
        cd $DEPLOY_DIR
        
        # Если директория уже существует, обновляем
        if [ -d '.git' ]; then
            echo '🔄 Обновление существующего репозитория...'
            git fetch origin
            git reset --hard origin/main
            git pull origin main
        else
            echo '📥 Клонирование репозитория...'
            git clone $REPO_URL .
        fi
        
        echo '✅ Репозиторий обновлен'
    "
}

# Создание production .env файла
create_env_file() {
    echo "📝 Создание production .env файла..."
    
    run_on_server "
        cd $DEPLOY_DIR
        
        cat > .env.prod << 'EOL'
# Production Environment
NODE_ENV=production

# Database (PostgreSQL)
POSTGRES_DB=booksmood
POSTGRES_USER=booksmood
POSTGRES_PASSWORD=\${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}
DATABASE_URL=postgresql://booksmood:\${POSTGRES_PASSWORD}@postgres:5432/booksmood

# Redis Cache
REDIS_PASSWORD=\${REDIS_PASSWORD:-$(openssl rand -base64 32)}
REDIS_URL=redis://:\${REDIS_PASSWORD}@redis:6379

# JWT Secret
JWT_SECRET=\${JWT_SECRET:-$(openssl rand -base64 48)}

# Telegram (ОБЯЗАТЕЛЬНО ЗАПОЛНИТЬ!)
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
TELEGRAM_BOT_USERNAME=your_bot_username

# S3 Storage (для production рекомендуется AWS S3)
S3_ENDPOINT=\${S3_ENDPOINT:-http://minio:9000}
S3_ACCESS_KEY=\${S3_ACCESS_KEY:-minioadmin}
S3_SECRET_KEY=\${S3_SECRET_KEY:-$(openssl rand -base64 32)}
S3_BUCKET=\${S3_BUCKET:-booksmood-audio}
S3_REGION=\${S3_REGION:-us-east-1}

# API URLs
FRONTEND_API_URL=https://$SERVER_HOST:3001
ADMIN_API_URL=https://$SERVER_HOST:3001

# Security
CORS_ORIGIN=https://$SERVER_HOST:3000
RATE_LIMIT_WINDOW=3600000
RATE_LIMIT_MAX=1000

# Monitoring
SENTRY_DSN=
LOG_LEVEL=warn
EOL
        
        echo '✅ .env.prod файл создан'
        echo '⚠️  ВАЖНО: Не забудьте заполнить TELEGRAM_BOT_TOKEN!'
    "
}

# Сборка и запуск контейнеров
deploy_application() {
    echo "🔧 Сборка и развертывание приложения..."
    
    run_on_server "
        cd $DEPLOY_DIR
        
        # Останавливаем старые контейнеры
        docker-compose -f docker-compose.prod.yml down || true
        
        # Удаляем старые образы для пересборки
        docker-compose -f docker-compose.prod.yml build --no-cache
        
        # Запускаем сервисы
        docker-compose -f docker-compose.prod.yml up -d
        
        # Ждем запуска базы данных
        echo '⏳ Ожидание готовности базы данных...'
        sleep 10
        
        # Выполняем миграции
        echo '📊 Выполнение миграций базы данных...'
        docker-compose -f docker-compose.prod.yml exec -T backend npx prisma migrate deploy || true
        
        echo '✅ Приложение развернуто'
    "
}

# Проверка статуса развертывания
check_deployment() {
    echo "🏥 Проверка состояния сервисов..."
    
    run_on_server "
        cd $DEPLOY_DIR
        
        echo '📊 Статус контейнеров:'
        docker-compose -f docker-compose.prod.yml ps
        
        echo ''
        echo '🔗 Доступные URL:'
        echo '  Frontend: http://$SERVER_HOST:3000'
        echo '  Admin Panel: http://$SERVER_HOST:3002'  
        echo '  Backend API: http://$SERVER_HOST:3001'
        echo '  MinIO Console: http://$SERVER_HOST:9001'
        
        echo ''
        echo '🔍 Health Check API:'
        if curl -f -s http://localhost:3001/health > /dev/null 2>&1; then
            echo '  ✅ Backend API: OK'
        else
            echo '  ❌ Backend API: FAILED'
        fi
    "
}

# Показать логи
show_logs() {
    echo "📋 Последние логи приложения:"
    run_on_server "
        cd $DEPLOY_DIR
        docker-compose -f docker-compose.prod.yml logs --tail=50
    "
}

# Основная функция
main() {
    case "${1:-deploy}" in
        "check")
            check_server
            ;;
        "prepare")
            check_server
            prepare_server
            ;;
        "update")
            check_server
            update_repository
            ;;
        "deploy")
            check_server
            prepare_server
            update_repository
            create_env_file
            deploy_application
            check_deployment
            echo ""
            echo "🎉 Развертывание завершено!"
            echo ""
            echo "📝 Следующие шаги:"
            echo "1. Подключитесь к серверу: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST"
            echo "2. Отредактируйте файл: nano $DEPLOY_DIR/.env.prod"
            echo "3. Добавьте ваш TELEGRAM_BOT_TOKEN"
            echo "4. Перезапустите: cd $DEPLOY_DIR && docker-compose -f docker-compose.prod.yml restart"
            ;;
        "status")
            check_server
            check_deployment
            ;;
        "logs")
            check_server
            show_logs
            ;;
        "restart")
            check_server
            run_on_server "cd $DEPLOY_DIR && docker-compose -f docker-compose.prod.yml restart"
            check_deployment
            ;;
        *)
            echo "Использование: $0 [check|prepare|update|deploy|status|logs|restart]"
            echo ""
            echo "Команды:"
            echo "  check   - Проверить доступность сервера"
            echo "  prepare - Подготовить сервер (установить Docker, etc)"
            echo "  update  - Обновить код из репозитория"
            echo "  deploy  - Полное развертывание (по умолчанию)"
            echo "  status  - Показать статус сервисов"
            echo "  logs    - Показать логи приложения"
            echo "  restart - Перезапустить сервисы"
            exit 1
            ;;
    esac
}

main "$@" 