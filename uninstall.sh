#!/bin/bash

# BooksMood - Скрипт полной остановки и очистки
# Удаляет проект, контейнеры, данные и настройки

set -e

# Конфигурация
PROJECT_DIR="/opt/booksmood"
PROJECT_NAME="booksmood"
SERVICE_NAME="booksmood"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${RED}🗑️  BooksMood - Остановка и очистка${NC}"
echo -e "${RED}===================================${NC}"
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
}

# Проверка прав sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        log "Запуск с правами sudo..."
        exec sudo "$0" "$@"
    fi
}

# Подтверждение удаления
confirm_removal() {
    echo -e "${YELLOW}⚠️  ВНИМАНИЕ! Это действие удалит:${NC}"
    echo "   • Все контейнеры Docker проекта BooksMood"
    echo "   • Все образы Docker проекта"
    echo "   • Все данные базы данных и файлы"
    echo "   • Папку проекта: $PROJECT_DIR"
    echo "   • Systemd службу"
    echo "   • Пользователя системы"
    echo ""
    
    if [[ "${FORCE:-}" == "true" ]]; then
        log "Принудительный режим активен, пропускаем подтверждение"
        return
    fi
    
    read -p "Вы уверены, что хотите продолжить? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Операция отменена"
        exit 0
    fi
}

# Остановка systemd службы
stop_systemd_service() {
    if systemctl is-enabled "$SERVICE_NAME.service" &>/dev/null; then
        log "Остановка systemd службы..."
        systemctl stop "$SERVICE_NAME.service" || true
        systemctl disable "$SERVICE_NAME.service" || true
        
        if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
            rm -f "/etc/systemd/system/$SERVICE_NAME.service"
            systemctl daemon-reload
            log "Systemd служба удалена"
        fi
    else
        log "Systemd служба не найдена"
    fi
}

# Остановка и удаление контейнеров
stop_containers() {
    log "Остановка и удаление контейнеров..."
    
    if [ -d "$PROJECT_DIR" ]; then
        cd "$PROJECT_DIR"
        
        # Остановка контейнеров через docker-compose
        if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
            log "Остановка через docker-compose..."
            docker-compose down --volumes --remove-orphans || true
        fi
        
        # Принудительная остановка всех контейнеров проекта
        if command -v docker &> /dev/null; then
            log "Принудительная остановка контейнеров BooksMood..."
            
            # Остановка контейнеров по имени проекта
            docker ps -a --filter "name=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker stop || true
            docker ps -a --filter "name=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker rm -f || true
            
            # Остановка контейнеров по label (если есть)
            docker ps -a --filter "label=project=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker stop || true
            docker ps -a --filter "label=project=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker rm -f || true
            
            log "Контейнеры остановлены и удалены"
        fi
    else
        warn "Директория проекта не найдена: $PROJECT_DIR"
    fi
}

# Удаление образов Docker
remove_images() {
    if command -v docker &> /dev/null; then
        log "Удаление образов Docker..."
        
        # Удаление образов по имени проекта
        docker images --filter "reference=${PROJECT_NAME}*" --format "{{.ID}}" | xargs -r docker rmi -f || true
        docker images --filter "reference=*${PROJECT_NAME}*" --format "{{.ID}}" | xargs -r docker rmi -f || true
        
        # Удаление образов по label
        docker images --filter "label=project=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker rmi -f || true
        
        log "Образы Docker удалены"
    fi
}

# Удаление volumes
remove_volumes() {
    if command -v docker &> /dev/null; then
        log "Удаление Docker volumes..."
        
        # Удаление именованных volumes проекта
        docker volume ls --filter "name=${PROJECT_NAME}" --format "{{.Name}}" | xargs -r docker volume rm -f || true
        docker volume ls --filter "label=project=${PROJECT_NAME}" --format "{{.Name}}" | xargs -r docker volume rm -f || true
        
        # Удаление неиспользуемых volumes
        docker volume prune -f || true
        
        log "Docker volumes удалены"
    fi
}

# Удаление сетей Docker
remove_networks() {
    if command -v docker &> /dev/null; then
        log "Удаление Docker сетей..."
        
        # Удаление сетей проекта
        docker network ls --filter "name=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker network rm || true
        docker network ls --filter "label=project=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker network rm || true
        
        # Очистка неиспользуемых сетей
        docker network prune -f || true
        
        log "Docker сети удалены"
    fi
}

# Удаление файлов проекта
remove_project_files() {
    if [ -d "$PROJECT_DIR" ]; then
        log "Удаление файлов проекта: $PROJECT_DIR"
        
        # Создание резервной копии .env (опционально)
        if [ -f "$PROJECT_DIR/.env" ]; then
            warn "Создание резервной копии .env..."
            cp "$PROJECT_DIR/.env" "/tmp/${PROJECT_NAME}-env-backup-$(date +%Y%m%d-%H%M%S)" || true
        fi
        
        # Удаление директории проекта
        rm -rf "$PROJECT_DIR"
        log "Файлы проекта удалены"
    else
        log "Директория проекта не найдена"
    fi
}

# Удаление пользователя системы
remove_system_user() {
    if id "$PROJECT_NAME" &>/dev/null; then
        log "Удаление пользователя системы: $PROJECT_NAME"
        
        # Завершение процессов пользователя
        pkill -u "$PROJECT_NAME" || true
        sleep 2
        
        # Удаление пользователя
        userdel "$PROJECT_NAME" || true
        
        # Удаление домашней директории пользователя (если существует и отличается от PROJECT_DIR)
        USER_HOME=$(eval echo "~$PROJECT_NAME" 2>/dev/null) || USER_HOME=""
        if [ -n "$USER_HOME" ] && [ "$USER_HOME" != "$PROJECT_DIR" ] && [ -d "$USER_HOME" ]; then
            rm -rf "$USER_HOME" || true
        fi
        
        log "Пользователь системы удален"
    else
        log "Пользователь системы не найден"
    fi
}

# Очистка файрвола
cleanup_firewall() {
    log "Очистка правил файрвола..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian UFW
        ufw delete allow 3000/tcp || true
        ufw delete allow 3001/tcp || true
        ufw delete allow 3002/tcp || true
        ufw delete allow 9001/tcp || true
        log "UFW правила удалены"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewalld
        firewall-cmd --permanent --remove-port=3000/tcp || true
        firewall-cmd --permanent --remove-port=3001/tcp || true
        firewall-cmd --permanent --remove-port=3002/tcp || true
        firewall-cmd --permanent --remove-port=9001/tcp || true
        firewall-cmd --reload || true
        log "Firewalld правила удалены"
    else
        warn "Файрвол не найден, правила не очищены"
    fi
}

# Очистка логов
cleanup_logs() {
    log "Очистка логов..."
    
    # Очистка журнала systemd
    journalctl --vacuum-time=1d || true
    
    # Очистка логов Docker
    if command -v docker &> /dev/null; then
        docker system prune -a -f --volumes || true
    fi
    
    log "Логи очищены"
}

# Опциональное удаление Docker
remove_docker() {
    if [[ "${REMOVE_DOCKER:-}" == "true" ]]; then
        log "Удаление Docker..."
        
        # Остановка Docker
        systemctl stop docker || true
        systemctl disable docker || true
        
        # Определение ОС для удаления
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$ID
        fi
        
        case $OS in
            ubuntu|debian)
                apt-get remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
                apt-get autoremove -y || true
                ;;
            centos|rhel|rocky|almalinux)
                yum remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
                ;;
        esac
        
        # Удаление конфигурационных файлов
        rm -rf /var/lib/docker
        rm -rf /var/lib/containerd
        rm -rf /etc/docker
        rm -rf ~/.docker
        
        # Удаление docker-compose
        rm -f /usr/local/bin/docker-compose
        rm -f /usr/bin/docker-compose
        
        log "Docker полностью удален"
    else
        log "Docker оставлен в системе (для удаления используйте --remove-docker)"
    fi
}

# Проверка оставшихся следов
check_cleanup() {
    log "Проверка результатов очистки..."
    
    echo ""
    echo -e "${BLUE}📋 Результаты очистки:${NC}"
    
    # Проверка контейнеров
    if command -v docker &> /dev/null; then
        CONTAINERS=$(docker ps -a --filter "name=${PROJECT_NAME}" --format "{{.Names}}" | wc -l)
        if [ "$CONTAINERS" -eq 0 ]; then
            echo -e "   ✅ Контейнеры: удалены"
        else
            echo -e "   ❌ Контейнеры: найдены оставшиеся ($CONTAINERS)"
        fi
        
        # Проверка образов
        IMAGES=$(docker images --filter "reference=*${PROJECT_NAME}*" --format "{{.Repository}}" | wc -l)
        if [ "$IMAGES" -eq 0 ]; then
            echo -e "   ✅ Образы: удалены"
        else
            echo -e "   ❌ Образы: найдены оставшиеся ($IMAGES)"
        fi
        
        # Проверка volumes
        VOLUMES=$(docker volume ls --filter "name=${PROJECT_NAME}" --format "{{.Name}}" | wc -l)
        if [ "$VOLUMES" -eq 0 ]; then
            echo -e "   ✅ Volumes: удалены"
        else
            echo -e "   ❌ Volumes: найдены оставшиеся ($VOLUMES)"
        fi
    fi
    
    # Проверка файлов
    if [ -d "$PROJECT_DIR" ]; then
        echo -e "   ❌ Файлы проекта: директория $PROJECT_DIR всё ещё существует"
    else
        echo -e "   ✅ Файлы проекта: удалены"
    fi
    
    # Проверка пользователя
    if id "$PROJECT_NAME" &>/dev/null; then
        echo -e "   ❌ Пользователь: $PROJECT_NAME всё ещё существует"
    else
        echo -e "   ✅ Пользователь: удален"
    fi
    
    # Проверка службы
    if systemctl is-enabled "$SERVICE_NAME.service" &>/dev/null; then
        echo -e "   ❌ Служба: $SERVICE_NAME всё ещё активна"
    else
        echo -e "   ✅ Служба: удалена"
    fi
    
    echo ""
}

# Вывод финальной информации
show_final_info() {
    echo ""
    echo -e "${PURPLE}🎉 Очистка BooksMood завершена!${NC}"
    echo -e "${PURPLE}===============================${NC}"
    echo ""
    
    if [ -f "/tmp/${PROJECT_NAME}-env-backup-"* ] 2>/dev/null; then
        echo -e "${GREEN}💾 Резервная копия .env сохранена в /tmp/${NC}"
        ls -la /tmp/${PROJECT_NAME}-env-backup-* 2>/dev/null || true
        echo ""
    fi
    
    echo -e "${GREEN}✅ Успешно удалено:${NC}"
    echo "   • Все контейнеры и образы Docker"
    echo "   • Все данные и файлы проекта"
    echo "   • Systemd служба"
    echo "   • Пользователь системы"
    echo "   • Правила файрвола"
    echo ""
    
    if [[ "${REMOVE_DOCKER:-}" != "true" ]]; then
        echo -e "${YELLOW}ℹ️  Docker оставлен в системе${NC}"
        echo "   Для полного удаления запустите:"
        echo "   bash uninstall.sh --remove-docker"
        echo ""
    fi
    
    echo -e "${GREEN}🔄 Для повторной установки используйте:${NC}"
    echo "   bash install.sh"
    echo ""
}

# Главная функция
main() {
    log "Начало очистки BooksMood..."
    
    check_sudo "$@"
    confirm_removal
    stop_systemd_service
    stop_containers
    remove_images
    remove_volumes
    remove_networks
    remove_project_files
    remove_system_user
    cleanup_firewall
    cleanup_logs
    remove_docker
    check_cleanup
    show_final_info
}

# Обработка параметров командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --remove-docker)
            REMOVE_DOCKER=true
            shift
            ;;
        --help|-h)
            echo "BooksMood - Скрипт очистки"
            echo ""
            echo "Использование:"
            echo "  bash uninstall.sh                # Стандартная очистка"
            echo "  bash uninstall.sh --force        # Без подтверждения"
            echo "  bash uninstall.sh --remove-docker # С удалением Docker"
            echo "  bash uninstall.sh --help         # Эта справка"
            echo ""
            echo "Параметры:"
            echo "  --force         Пропустить подтверждение удаления"
            echo "  --remove-docker Удалить Docker из системы"
            echo ""
            exit 0
            ;;
        *)
            error "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

# Запуск главной функции
main 