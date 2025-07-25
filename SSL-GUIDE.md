# 🔒 SSL сертификат для app.booksmood.ru

## 🚀 Быстрая настройка (Рекомендуется)

### Автоматическая установка:

```bash
# Скачайте проект и запустите автоматический скрипт
git clone https://github.com/Cossomoj/booksmood.git
cd booksmood
sudo chmod +x scripts/ssl-setup.sh
sudo ./scripts/ssl-setup.sh
```

**Что делает скрипт:**
- ✅ Устанавливает Nginx и Certbot
- ✅ Создает конфигурацию Nginx
- ✅ Получает SSL сертификат от Let's Encrypt
- ✅ Настраивает автообновление
- ✅ Применяет настройки безопасности

## 📋 Предварительные требования

**ВАЖНО! Перед запуском убедитесь:**

1. **DNS настроен**: `app.booksmood.ru` → IP вашего сервера
2. **Порты открыты**: 80 (HTTP) и 443 (HTTPS)
3. **Root доступ**: скрипт требует sudo права
4. **Чистый сервер**: никакого другого веб-сервера на портах 80/443

### Проверка DNS:
```bash
nslookup app.booksmood.ru
dig app.booksmood.ru
```

### Проверка портов:
```bash
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## 🛠 Ручная установка

Если автоматический скрипт не сработал:

### 1. Остановите веб-серверы:
```bash
sudo systemctl stop nginx apache2 2>/dev/null || true
```

### 2. Запустите ручную установку:
```bash
sudo chmod +x scripts/ssl-manual.sh
sudo ./scripts/ssl-manual.sh
```

### 3. Создайте конфигурацию Nginx:
```bash
sudo nano /etc/nginx/sites-available/app.booksmood.ru
```

Вставьте конфигурацию:
```nginx
# HTTP редирект
server {
    listen 80;
    server_name app.booksmood.ru;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name app.booksmood.ru;

    ssl_certificate /etc/letsencrypt/live/app.booksmood.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.booksmood.ru/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/booksmood/app/static/;
        expires 30d;
    }
}
```

### 4. Активируйте сайт:
```bash
sudo ln -s /etc/nginx/sites-available/app.booksmood.ru /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl start nginx
```

## 🔍 Проверка SSL

### Автоматическая проверка:
```bash
chmod +x scripts/ssl-check.sh
./scripts/ssl-check.sh
```

### Ручная проверка:
```bash
# Проверка сертификата
openssl s_client -connect app.booksmood.ru:443 -servername app.booksmood.ru

# Проверка API
curl -I https://app.booksmood.ru/health

# Проверка Certbot
sudo certbot certificates
```

## 🔄 Обновление сертификата

### Автоматическое обновление (уже настроено):
```bash
# Проверить cron задачу
crontab -l | grep certbot

# Добавить если нет
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
```

### Ручное обновление:
```bash
sudo certbot renew
sudo systemctl reload nginx
```

## ❌ Устранение проблем

### Проблема: "Domain validation failed"
```bash
# Проверьте DNS
dig app.booksmood.ru

# Проверьте порт 80
sudo netstat -tlnp | grep :80

# Остановите другие веб-серверы
sudo systemctl stop apache2
```

### Проблема: "Nginx configuration test failed"
```bash
# Проверьте синтаксис
sudo nginx -t

# Проверьте логи
sudo journalctl -u nginx -f
```

### Проблема: "Certificate expired"
```bash
# Обновите принудительно
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

## 📱 Настройка Telegram бота

После успешной установки SSL:

### 1. Настройте Web App в BotFather:
```
/setmenubutton
@booksmoodbot
📚 Открыть аудиокниги
https://app.booksmood.ru
```

### 2. Добавьте домен:
```
/setdomain
@booksmoodbot
app.booksmood.ru
```

## 🔐 Безопасность

### Настройки в конфигурации:
- ✅ **TLS 1.2/1.3** - современные протоколы
- ✅ **HSTS** - принудительный HTTPS
- ✅ **Security Headers** - защита от атак
- ✅ **Gzip сжатие** - оптимизация скорости

### Дополнительная защита админ панели:
```nginx
location /admin/ {
    # Ограничить доступ по IP
    allow 192.168.1.0/24;  # Ваша сеть
    allow YOUR_IP_HERE;    # Ваш IP
    deny all;
    
    proxy_pass http://localhost:8000;
    # ... другие настройки
}
```

## 📊 Мониторинг

### Проверка статуса:
```bash
# SSL сертификат
./scripts/ssl-check.sh

# Сервисы
sudo systemctl status nginx
sudo systemctl status booksmood

# Логи
sudo journalctl -u nginx -f
sudo journalctl -u booksmood -f
```

### Онлайн проверка:
- 🔗 https://www.ssllabs.com/ssltest/
- 🔗 https://observatory.mozilla.org/
- 🔗 https://securityheaders.com/

## 📞 Поддержка

При проблемах проверьте:
1. **DNS**: `app.booksmood.ru` указывает на сервер
2. **Firewall**: порты 80/443 открыты
3. **Сервисы**: Nginx и BooksMood запущены
4. **Логи**: нет ошибок в журналах

**Полезные команды:**
```bash
# Перезапуск всего
sudo systemctl restart nginx
sudo systemctl restart booksmood

# Проверка конфигурации
sudo nginx -t
```

🎉 **После настройки ваш сайт будет доступен по адресу: https://app.booksmood.ru** 