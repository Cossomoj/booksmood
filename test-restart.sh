#!/bin/bash
set -e

echo "🔄 Тестирование автоматического перезапуска nginx после обновления контейнера"
echo "==============================================================================="

VPS_HOST="user1@213.171.25.85"
SSH_KEY="~/.ssh/id_ed25519"

echo "📋 Шаг 1: Проверяем текущий статус HTTPS..."
if curl -s -I https://app.booksmood.ru | grep -q "HTTP/2"; then
    echo "✅ HTTPS работает до обновления"
else
    echo "❌ HTTPS не работает до обновления"
    exit 1
fi

echo ""
echo "📋 Шаг 2: Пересобираем и перезапускаем контейнер..."
ssh -i $SSH_KEY $VPS_HOST "cd /home/user1 && sudo docker-compose down"
ssh -i $SSH_KEY $VPS_HOST "cd /home/user1 && sudo docker-compose build --no-cache"
ssh -i $SSH_KEY $VPS_HOST "cd /home/user1 && sudo docker-compose up -d"

echo ""
echo "📋 Шаг 3: Ждем запуска сервисов..."
sleep 15

echo ""
echo "📋 Шаг 4: Проверяем логи SSL скрипта..."
ssh -i $SSH_KEY $VPS_HOST "sudo docker logs booksmood_app | grep -A 20 'SSL сертификаты'"

echo ""
echo "📋 Шаг 5: Проверяем финальный статус HTTPS..."
sleep 10

if curl -s -I https://app.booksmood.ru | grep -q "HTTP/2"; then
    echo "✅ HTTPS работает после обновления - автоматический перезапуск nginx успешен!"
    echo ""
    echo "🎉 Тест пройден! Nginx автоматически перезапускается при обновлении контейнера."
else
    echo "❌ HTTPS не работает после обновления"
    echo "📋 Проверяем статус сервисов..."
    ssh -i $SSH_KEY $VPS_HOST "sudo docker exec booksmood_app pgrep nginx || echo 'nginx не запущен'"
    exit 1
fi

echo ""
echo "📊 Дополнительные проверки:"
echo "🌐 Основной сайт: https://app.booksmood.ru"
echo "⚙️ Админ панель: http://213.171.25.85:8088/admin/dashboard" 