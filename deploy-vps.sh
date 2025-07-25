#!/bin/bash

# 🚀 Развертывание BooksMood на VPS
# =================================

set -e

VPS_IP="213.171.25.85"
VPS_USER="user1"
SSH_KEY="~/.ssh/id_ed25519"

echo "🚀 Развертывание BooksMood на VPS: $VPS_IP"
echo "=========================================="

# Функция для выполнения команд на VPS
run_on_vps() {
    ssh -i $SSH_KEY $VPS_USER@$VPS_IP "$1"
}

# Копирование файла на VPS
copy_to_vps() {
    scp -i $SSH_KEY "$1" $VPS_USER@$VPS_IP:"$2"
}

echo "📋 1. Проверка подключения к VPS..."
if run_on_vps "echo 'VPS доступен'"; then
    echo "✅ Подключение к VPS успешно"
else
    echo "❌ Не удается подключиться к VPS"
    exit 1
fi

echo "📦 2. Установка Docker (если не установлен)..."
run_on_vps "
    if ! command -v docker &> /dev/null; then
        echo 'Установка Docker...'
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker \$USER
        rm get-docker.sh
    else
        echo 'Docker уже установлен'
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo 'Установка Docker Compose...'
        sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo 'Docker Compose уже установлен'
    fi
"

echo "📁 3. Создание директории проекта..."
run_on_vps "
    sudo mkdir -p /opt/booksmood
    sudo chown \$USER:\$USER /opt/booksmood
    cd /opt/booksmood
"

echo "🔄 4. Клонирование репозитория..."
run_on_vps "
    cd /opt/booksmood
    if [ -d '.git' ]; then
        echo 'Обновление существующего репозитория...'
        git pull origin master
    else
        echo 'Клонирование репозитория...'
        git clone https://github.com/Cossomoj/booksmood.git .
    fi
"

echo "🚀 5. Запуск BooksMood..."
run_on_vps "
    cd /opt/booksmood
    sudo docker-compose down 2>/dev/null || true
    sudo docker-compose up --build -d
"

echo "⏳ 6. Ожидание запуска (30 секунд)..."
sleep 30

echo "🔍 7. Проверка развертывания..."
if run_on_vps "curl -s http://localhost/health > /dev/null"; then
    echo "✅ BooksMood успешно развернут!"
else
    echo "⚠️ Сервис может еще запускаться..."
fi

echo ""
echo "🎉 Развертывание завершено!"
echo "=========================="
echo "🌐 HTTP: http://$VPS_IP"
echo "📚 API: http://$VPS_IP:8000"
echo "⚙️ Админ: http://$VPS_IP/admin/login"
echo "📖 Docs: http://$VPS_IP:8000/docs"
echo ""
echo "👤 Админ логин: admin / admin123"
echo ""
echo "📋 Полезные команды на VPS:"
echo "ssh -i $SSH_KEY $VPS_USER@$VPS_IP"
echo "cd /opt/booksmood"
echo "sudo docker-compose logs -f"
echo "sudo docker-compose restart" 