#!/bin/bash

# Быстрое развертывание BooksMood на сервер с локальной машины

set -e

# Конфигурация
SERVER_USER="user1"
SERVER_HOST="213.171.25.85"
SSH_KEY="~/.ssh/id_ed25519"

echo "🚀 BooksMood - Развертывание на сервер"
echo "======================================"
echo "📡 Сервер: $SERVER_USER@$SERVER_HOST"
echo ""

# Проверка подключения к серверу
echo "🔍 Проверка подключения к серверу..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo 'Подключение успешно'" 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу!"
    echo "Проверьте:"
    echo "  • SSH ключ: $SSH_KEY" 
    echo "  • IP адрес: $SERVER_HOST"
    echo "  • Пользователь: $SERVER_USER"
    exit 1
fi
echo "✅ Сервер доступен"

# Копируем скрипт развертывания на сервер
echo "📋 Копирование скрипта развертывания..."
scp -i "$SSH_KEY" scripts/server-deploy.sh "$SERVER_USER@$SERVER_HOST:/tmp/"

# Выполняем развертывание на сервере
echo "🚀 Запуск развертывания на сервере..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
    chmod +x /tmp/server-deploy.sh
    /tmp/server-deploy.sh deploy
    rm /tmp/server-deploy.sh
"

echo ""
echo "🎉 Развертывание завершено!"
echo ""
echo "🌐 Доступные URL:"
echo "  • Frontend: http://$SERVER_HOST:3000"
echo "  • Admin Panel: http://$SERVER_HOST:3002"
echo "  • Backend API: http://$SERVER_HOST:3001"
echo "  • MinIO Console: http://$SERVER_HOST:9001"
echo ""
echo "📝 Следующие шаги:"
echo "1. Подключитесь к серверу: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST"
echo "2. Отредактируйте .env файл: nano /opt/booksmood/.env.prod"
echo "3. Добавьте TELEGRAM_BOT_TOKEN"
echo "4. Перезапустите сервисы: cd /opt/booksmood && docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "🔧 Управление сервисами:"
echo "• Статус: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST 'cd /opt/booksmood && docker-compose -f docker-compose.prod.yml ps'"
echo "• Логи: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST 'cd /opt/booksmood && docker-compose -f docker-compose.prod.yml logs -f'"
echo "• Перезапуск: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST 'cd /opt/booksmood && docker-compose -f docker-compose.prod.yml restart'" 