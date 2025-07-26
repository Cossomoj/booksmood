#!/bin/bash
set -e

echo "🔍 Диагностика SSL для app.booksmood.ru"
echo "========================================"

# Проверяем подключение к VPS
echo "📡 Проверяем подключение к VPS..."
if ! ssh -i ~/.ssh/id_ed25519 -o ConnectTimeout=10 user1@213.171.25.85 "echo 'VPS доступен'" 2>/dev/null; then
    echo "❌ Не удается подключиться к VPS"
    exit 1
fi
echo "✅ VPS доступен"

# Проверяем наличие SSL сертификатов на VPS
echo ""
echo "🔐 Проверяем SSL сертификаты на VPS..."
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 << 'EOF'
echo "📁 Проверяем папку /opt/ssl-certs:"
ls -la /opt/ssl-certs/ 2>/dev/null || echo "❌ Папка /opt/ssl-certs не существует"

echo ""
echo "📋 Проверяем наличие сертификатов:"
if [ -f "/opt/ssl-certs/fullchain.pem" ] && [ -f "/opt/ssl-certs/privkey.pem" ]; then
    echo "✅ SSL сертификаты найдены"
    echo "📅 Срок действия сертификата:"
    openssl x509 -in /opt/ssl-certs/fullchain.pem -text -noout | grep "Not After" || echo "❌ Не удалось проверить срок действия"
else
    echo "❌ SSL сертификаты не найдены"
    echo "💡 Нужно сгенерировать сертификат:"
    echo "   bash /opt/ssl-certs/ssl-generate.sh"
fi
EOF

# Проверяем статус Docker контейнера
echo ""
echo "🐳 Проверяем статус Docker контейнера..."
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 << 'EOF'
cd /opt/booksmood
echo "📋 Статус контейнеров:"
sudo docker-compose ps

echo ""
echo "📋 Логи SSL проверки:"
sudo docker logs booksmood_app 2>/dev/null | grep -i ssl || echo "❌ Логи SSL не найдены"

echo ""
echo "📋 Логи nginx:"
sudo docker logs booksmood_app 2>/dev/null | grep -i nginx || echo "❌ Логи nginx не найдены"

echo ""
echo "🔍 Проверяем конфигурацию nginx в контейнере:"
sudo docker exec booksmood_app cat /etc/nginx/sites-available/default 2>/dev/null || echo "❌ Не удалось получить конфигурацию nginx"

echo ""
echo "🔍 Проверяем наличие SSL файлов в контейнере:"
sudo docker exec booksmood_app ls -la /etc/nginx/ssl/ 2>/dev/null || echo "❌ SSL файлы не найдены в контейнере"

echo ""
echo "🔍 Проверяем монтирование /host-ssl:"
sudo docker exec booksmood_app ls -la /host-ssl/ 2>/dev/null || echo "❌ /host-ssl не смонтирован"
EOF

# Проверяем доступность сайта
echo ""
echo "🌐 Проверяем доступность сайта..."
echo "📡 HTTP (порт 80):"
if curl -s -o /dev/null -w "%{http_code}" http://app.booksmood.ru; then
    echo "✅ HTTP доступен"
else
    echo "❌ HTTP недоступен"
fi

echo ""
echo "📡 HTTPS (порт 443):"
if curl -s -o /dev/null -w "%{http_code}" https://app.booksmood.ru; then
    echo "✅ HTTPS доступен"
else
    echo "❌ HTTPS недоступен"
fi

echo ""
echo "📡 Проверяем SSL сертификат:"
if openssl s_client -connect app.booksmood.ru:443 -servername app.booksmood.ru < /dev/null 2>/dev/null | openssl x509 -noout -dates; then
    echo "✅ SSL сертификат работает"
else
    echo "❌ SSL сертификат не работает"
fi

echo ""
echo "🔧 Рекомендации:"
echo "1. Если SSL сертификаты не найдены на VPS:"
echo "   ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85"
echo "   cd /opt/ssl-certs && sudo bash ssl-generate.sh"
echo ""
echo "2. Если контейнер не запущен:"
echo "   ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85"
echo "   cd /opt/booksmood && sudo docker-compose up -d"
echo ""
echo "3. Если нужно пересобрать контейнер:"
echo "   ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85"
echo "   cd /opt/booksmood && sudo docker-compose down && sudo docker-compose up --build -d" 