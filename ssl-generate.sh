#!/bin/bash
set -e

echo "🔐 Генерация SSL сертификата для app.booksmood.ru"
echo "=================================================="

# Создаем папку для сертификатов на VPS
sudo mkdir -p /opt/ssl-certs
cd /opt/ssl-certs

# Останавливаем Docker если работает на портах 80/443
echo "📋 Останавливаем Docker контейнеры..."
sudo docker stop $(sudo docker ps -q) 2>/dev/null || true

# Останавливаем nginx если работает
echo "📋 Останавливаем nginx..."
sudo systemctl stop nginx 2>/dev/null || true

# Устанавливаем certbot если не установлен
if ! command -v certbot &> /dev/null; then
    echo "📦 Устанавливаем certbot..."
    sudo apt update
    sudo apt install -y certbot
fi

# Генерируем сертификат
echo "🔐 Генерируем SSL сертификат..."
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email admin@booksmood.ru \
    --domains app.booksmood.ru \
    --cert-path /opt/ssl-certs/ \
    --key-path /opt/ssl-certs/ \
    --fullchain-path /opt/ssl-certs/ \
    --config-dir /opt/ssl-certs/config \
    --work-dir /opt/ssl-certs/work \
    --logs-dir /opt/ssl-certs/logs

# Копируем сертификаты в удобное место
echo "📋 Копируем сертификаты..."
sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/fullchain.pem /opt/ssl-certs/
sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/privkey.pem /opt/ssl-certs/
sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/cert.pem /opt/ssl-certs/
sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/chain.pem /opt/ssl-certs/

# Устанавливаем права
sudo chmod 644 /opt/ssl-certs/*.pem
sudo chown root:root /opt/ssl-certs/*.pem

echo "✅ SSL сертификат успешно создан!"
echo "📁 Сертификаты сохранены в: /opt/ssl-certs/"
echo "📋 Файлы:"
ls -la /opt/ssl-certs/*.pem

echo ""
echo "🚀 Теперь можно запустить Docker:"
echo "cd /opt/booksmood && sudo docker-compose up --build -d"

# Создаем скрипт для обновления сертификата
cat > /opt/ssl-certs/renew.sh << 'EOF'
#!/bin/bash
echo "🔄 Обновление SSL сертификата..."
sudo docker stop $(sudo docker ps -q) 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

sudo certbot renew \
    --config-dir /opt/ssl-certs/config \
    --work-dir /opt/ssl-certs/work \
    --logs-dir /opt/ssl-certs/logs

if [ $? -eq 0 ]; then
    sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/fullchain.pem /opt/ssl-certs/
    sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/privkey.pem /opt/ssl-certs/
    sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/cert.pem /opt/ssl-certs/
    sudo cp /opt/ssl-certs/config/live/app.booksmood.ru/chain.pem /opt/ssl-certs/
    sudo chmod 644 /opt/ssl-certs/*.pem
    echo "✅ Сертификат обновлен успешно!"
    echo "🔄 Перезапускаем Docker..."
    cd /opt/booksmood && sudo docker-compose up -d
else
    echo "❌ Ошибка обновления сертификата"
fi
EOF

sudo chmod +x /opt/ssl-certs/renew.sh
echo "💡 Скрипт обновления создан: /opt/ssl-certs/renew.sh" 