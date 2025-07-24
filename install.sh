#!/bin/bash

# BooksMood - Автоматическая установка и запуск на сервере
# Скрипт устанавливает Docker, клонирует проект и запускает его

set -e

# Конфигурация
REPO_URL="https://github.com/Cossomoj/booksmood.git"
PROJECT_DIR="/opt/booksmood"
PROJECT_NAME="booksmood"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 BooksMood - Установка и запуск${NC}"
echo -e "${BLUE}=================================${NC}"
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

# Определение ОС
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        log "Обнаружена ОС: $PRETTY_NAME"
    else
        error "Не удается определить операционную систему"
    fi
}

# Обновление системы
update_system() {
    log "Обновление системы..."
    
    case $OS in
        ubuntu|debian)
            apt-get update -y
            apt-get upgrade -y
            ;;
        centos|rhel|rocky|almalinux)
            yum update -y || dnf update -y
            ;;
        *)
            warn "Неподдерживаемая ОС для автообновления: $OS"
            ;;
    esac
}

# Установка зависимостей
install_dependencies() {
    log "Установка базовых зависимостей..."
    
    case $OS in
        ubuntu|debian)
            apt-get install -y curl wget git software-properties-common apt-transport-https ca-certificates gnupg lsb-release
            ;;
        centos|rhel|rocky|almalinux)
            yum install -y curl wget git || dnf install -y curl wget git
            ;;
        *)
            error "Неподдерживаемая ОС: $OS"
            ;;
    esac
}

# Установка Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log "Docker уже установлен: $(docker --version)"
        return
    fi
    
    log "Установка Docker..."
    
    case $OS in
        ubuntu|debian)
            # Удаление старых версий
            apt-get remove -y docker docker-engine docker.io containerd runc || true
            
            # Добавление репозитория Docker
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Установка Docker
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        centos|rhel|rocky|almalinux)
            # Удаление старых версий
            yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine || true
            
            # Установка репозитория
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # Установка Docker
            yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
    esac
    
    # Запуск и автозапуск Docker
    systemctl start docker
    systemctl enable docker
    
    log "Docker установлен: $(docker --version)"
}

# Установка Docker Compose (standalone)
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log "Docker Compose уже установлен: $(docker-compose --version)"
        return
    fi
    
    log "Установка Docker Compose..."
    
    # Получение последней версии
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    
    # Загрузка и установка
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Создание симлинка
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log "Docker Compose установлен: $(docker-compose --version)"
}

# Создание пользователя для проекта (опционально)
setup_project_user() {
    if id "$PROJECT_NAME" &>/dev/null; then
        log "Пользователь $PROJECT_NAME уже существует"
    else
        log "Создание пользователя $PROJECT_NAME..."
        useradd -r -s /bin/false -d $PROJECT_DIR $PROJECT_NAME || true
    fi
    
    # Добавление пользователя в группу docker
    usermod -aG docker $PROJECT_NAME || true
}

# Создание директории проекта
setup_project_directory() {
    log "Настройка директории проекта: $PROJECT_DIR"
    
    # Создание директории
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # Клонирование репозитория
    if [ -d ".git" ]; then
        log "Обновление существующего репозитория..."
        git pull origin main || git pull origin master
    else
        log "Клонирование репозитория..."
        git clone $REPO_URL .
    fi
    
    # Права доступа
    chown -R $PROJECT_NAME:$PROJECT_NAME $PROJECT_DIR || true
}

# Настройка окружения
setup_environment() {
    log "Настройка файла окружения..."
    
    cd $PROJECT_DIR
    
    # Генерация безопасных паролей (только буквы и цифры)
    generate_safe_password() {
        openssl rand -hex 16
    }
    
    # Создание .env файла если его нет
    if [ ! -f ".env" ]; then
        log "Создание .env файла..."
        
        # Генерируем безопасные пароли
        JWT_SECRET=$(generate_safe_password)$(generate_safe_password)
        SESSION_SECRET=$(generate_safe_password)
        MINIO_PASSWORD=$(generate_safe_password)
        MINIO_SECRET=$(generate_safe_password)
        
        cat > .env << EOF
# ==============================================
# TELEGRAM BOT НАСТРОЙКИ
# ==============================================
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/webhook

# ==============================================
# DATABASE НАСТРОЙКИ (SQLite)
# ==============================================
DATABASE_URL=file:./data/database.db

# ==============================================
# SECURITY НАСТРОЙКИ
# ==============================================
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRES_IN=7d
SESSION_SECRET=${SESSION_SECRET}
RATE_LIMIT_WINDOW=3600000
RATE_LIMIT_MAX=100

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
        warn "⚠️  ВАЖНО: Отредактируйте файл .env и добавьте свой TELEGRAM_BOT_TOKEN!"
        warn "   Получить токен можно у @BotFather в Telegram"
    else
        log ".env файл уже существует"
    fi
}

# Настройка файрвола
setup_firewall() {
    log "Настройка файрвола..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian UFW
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 3000/tcp
        ufw allow 3001/tcp
        ufw allow 3002/tcp
        ufw allow 9001/tcp
        ufw --force enable
        log "UFW файрвол настроен"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewalld
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-port=22/tcp
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=3001/tcp
        firewall-cmd --permanent --add-port=3002/tcp
        firewall-cmd --permanent --add-port=9001/tcp
        firewall-cmd --reload
        log "Firewalld настроен"
    else
        warn "Файрвол не найден, настройте порты вручную:"
        warn "  22 (SSH), 80 (HTTP), 443 (HTTPS)"
        warn "  3000 (Frontend), 3001 (API), 3002 (Admin), 9001 (MinIO)"
    fi
}

# Запуск проекта
start_project() {
    log "Запуск проекта BooksMood..."
    
    cd $PROJECT_DIR
    
    # Остановка существующих контейнеров
    docker-compose down || true
    
    # Сборка и запуск
    docker-compose up -d --build
    
    # Ожидание запуска
    log "Ожидание запуска сервисов..."
    sleep 30
    
    # Проверка статуса
    log "Статус контейнеров:"
    docker-compose ps
    
    log "Инициализация базы данных..."
    docker-compose exec -T backend npm run db:migrate || true
    docker-compose exec -T backend npm run db:seed || true
}

# Создание systemd службы
create_systemd_service() {
    log "Создание systemd службы..."
    
    cat > /etc/systemd/system/booksmood.service << EOF
[Unit]
Description=BooksMood Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable booksmood.service
    log "Systemd служба создана и включена"
}

# Вывод финальной информации
show_final_info() {
    echo ""
    echo -e "${PURPLE}🎉 BooksMood успешно установлен и запущен!${NC}"
    echo -e "${PURPLE}============================================${NC}"
    echo ""
    echo -e "${GREEN}📱 Приложение доступно по адресам:${NC}"
    echo -e "   Frontend:    http://$(curl -s ifconfig.me):3000"
    echo -e "   API:         http://$(curl -s ifconfig.me):3001"
    echo -e "   Admin:       http://$(curl -s ifconfig.me):3002"
    echo -e "   MinIO:       http://$(curl -s ifconfig.me):9001"
    echo ""
    echo -e "${GREEN}🔧 Управление проектом:${NC}"
    echo -e "   Статус:      cd $PROJECT_DIR && docker-compose ps"
    echo -e "   Перезапуск:  cd $PROJECT_DIR && docker-compose restart"
    echo -e "   Остановка:   cd $PROJECT_DIR && docker-compose down"
    echo -e "   Логи:        cd $PROJECT_DIR && docker-compose logs -f"
    echo ""
    echo -e "${YELLOW}⚠️  НЕ ЗАБУДЬТЕ:${NC}"
    echo -e "   1. Отредактировать $PROJECT_DIR/.env"
    echo -e "   2. Добавить TELEGRAM_BOT_TOKEN от @BotFather"
    echo -e "   3. Настроить домен и SSL (при необходимости)"
    echo ""
    echo -e "${GREEN}✅ Установка завершена!${NC}"
}

# Главная функция
main() {
    log "Начало установки BooksMood..."
    
    check_sudo "$@"
    detect_os
    update_system
    install_dependencies
    install_docker
    install_docker_compose
    setup_project_user
    setup_project_directory
    setup_environment
    setup_firewall
    start_project
    create_systemd_service
    show_final_info
}

# Обработка параметров командной строки
case "${1:-}" in
    --help|-h)
        echo "BooksMood - Автоматическая установка"
        echo ""
        echo "Использование:"
        echo "  bash install.sh          # Полная установка"
        echo "  bash install.sh --help   # Эта справка"
        echo ""
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 