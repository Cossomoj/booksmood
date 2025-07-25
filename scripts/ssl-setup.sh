#!/bin/bash

# 🔒 SSL Setup для app.booksmood.ru
# ===================================

set -e

DOMAIN="app.booksmood.ru"
EMAIL="admin@booksmood.ru"  # Замените на ваш email
WEBROOT="/var/www/html"

echo "🔒 Настройка SSL сертификата для $DOMAIN"
echo "=================================================="

# Проверка прав суперпользователя
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установка Nginx (если не установлен)
if ! command -v nginx &> /dev/null; then
    echo "🔧 Установка Nginx..."
    apt install nginx -y
    systemctl enable nginx
    systemctl start nginx
else
    echo "✅ Nginx уже установлен"
fi

# Установка Certbot
echo "🔧 Установка Certbot..."
apt install certbot python3-certbot-nginx -y

# Создание базовой конфигурации Nginx
echo "📝 Создание конфигурации Nginx..."
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Временная конфигурация для получения сертификата
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }
}
EOF

# Включение сайта
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
echo "🔍 Проверка конфигурации Nginx..."
nginx -t

# Перезагрузка Nginx
systemctl reload nginx

# Создание webroot директории
mkdir -p $WEBROOT
chown -R www-data:www-data $WEBROOT

# Получение SSL сертификата
echo "🔐 Получение SSL сертификата от Let's Encrypt..."
certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect

# Обновление конфигурации Nginx с SSL
echo "📝 Обновление конфигурации с SSL..."
cat > /etc/nginx/sites-available/$DOMAIN << EOF
# HTTP редирект на HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS конфигурация
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL настройки безопасности
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS заголовки
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # Основная проксификация на FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket поддержка (если понадобится)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Статические файлы
    location /static/ {
        alias /opt/booksmood/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    # Безопасность для admin панели
    location /admin/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Дополнительная защита (опционально)
        # allow 192.168.1.0/24;  # Ваш IP
        # deny all;
    }
}
EOF

# Проверка и перезагрузка Nginx
nginx -t && systemctl reload nginx

# Настройка автообновления сертификата
echo "🔄 Настройка автообновления сертификата..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Проверка статуса сертификата
echo "🔍 Проверка сертификата..."
certbot certificates

echo ""
echo "🎉 SSL сертификат успешно установлен!"
echo "=================================================="
echo "🌍 Сайт доступен по адресу: https://$DOMAIN"
echo "🔐 Сертификат действителен 90 дней"
echo "🔄 Автообновление настроено"
echo ""
echo "📋 Следующие шаги:"
echo "1. Убедитесь что BooksMood API запущен на порту 8000"
echo "2. Проверьте https://$DOMAIN/health"
echo "3. Настройте Telegram бота на новый домен"
echo "" 