#!/bin/bash

# 🔍 Проверка SSL сертификата для app.booksmood.ru
# ================================================

DOMAIN="app.booksmood.ru"

echo "🔍 Проверка SSL сертификата для $DOMAIN"
echo "=================================================="

# Проверка через openssl
echo "📋 Информация о сертификате:"
timeout 10 openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | \
openssl x509 -noout -dates -subject -issuer 2>/dev/null || echo "❌ Не удалось подключиться к $DOMAIN:443"

echo ""

# Проверка через curl
echo "🌐 Проверка HTTPS соединения:"
if curl -I -s --max-time 10 https://$DOMAIN/health > /dev/null 2>&1; then
    echo "✅ HTTPS соединение работает"
    echo "📊 Ответ сервера:"
    curl -s --max-time 5 https://$DOMAIN/health | head -3
else
    echo "❌ HTTPS соединение не работает"
fi

echo ""

# Проверка сертификата Certbot (если установлен)
if command -v certbot &> /dev/null; then
    echo "📄 Сертификаты Certbot:"
    certbot certificates 2>/dev/null | grep -A 5 $DOMAIN || echo "❌ Сертификат не найден в Certbot"
else
    echo "⚠️ Certbot не установлен"
fi

echo ""

# Проверка конфигурации Nginx
if command -v nginx &> /dev/null; then
    echo "🔧 Конфигурация Nginx:"
    if nginx -t 2>/dev/null; then
        echo "✅ Конфигурация Nginx корректна"
    else
        echo "❌ Ошибка в конфигурации Nginx"
    fi
    
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx запущен"
    else
        echo "❌ Nginx не запущен"
    fi
else
    echo "⚠️ Nginx не установлен"
fi

echo ""
echo "🔗 Полезные команды:"
echo "   Обновить сертификат: sudo certbot renew"
echo "   Перезагрузить Nginx: sudo systemctl reload nginx"
echo "   Проверить логи: sudo journalctl -u nginx -f" 