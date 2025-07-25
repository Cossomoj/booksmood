#!/bin/bash

# 🔒 Ручное получение SSL сертификата для app.booksmood.ru
# ========================================================

set -e

DOMAIN="app.booksmood.ru"
EMAIL="admin@booksmood.ru"  # Замените на ваш email

echo "🔒 Ручное получение SSL сертификата для $DOMAIN"
echo "=================================================="

# Проверка прав суперпользователя
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

echo "📋 Предварительные требования:"
echo "1. Домен $DOMAIN должен указывать на этот сервер"
echo "2. Порт 80 должен быть открыт"
echo "3. Временно остановите другие веб-серверы"
echo ""
read -p "Все требования выполнены? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Выполните требования и попробуйте снова"
    exit 1
fi

# Установка Certbot (если не установлен)
if ! command -v certbot &> /dev/null; then
    echo "🔧 Установка Certbot..."
    apt update
    apt install certbot -y
fi

# Остановка веб-серверов
echo "⏸️ Остановка веб-серверов..."
systemctl stop nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true

# Получение сертификата в standalone режиме
echo "🔐 Получение SSL сертификата..."
certbot certonly \
    --standalone \
    --preferred-challenges http \
    -d $DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ Сертификат успешно получен!"
    echo ""
    echo "📁 Файлы сертификата:"
    echo "   Сертификат: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "   Приватный ключ: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo ""
    echo "🔗 Настройте ваш веб-сервер для использования этих файлов"
else
    echo "❌ Ошибка при получении сертификата"
    exit 1
fi

echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте Nginx с полученными сертификатами"
echo "2. Добавьте автообновление: 0 12 * * * /usr/bin/certbot renew --quiet"
echo "3. Проверьте: https://$DOMAIN" 