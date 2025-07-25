# 🚀 Развертывание в продакшн

## Настройки для app.booksmood.ru

### 1. Переменные окружения

Создайте файл `.env` с продакшн настройками:

```bash
# BooksMood Production Environment
# ================================

# Telegram Bot
BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY
TELEGRAM_BOT_USERNAME=booksmoodbot

# Security (ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ В ПРОДАКШН!)
SECRET_KEY=your-super-secure-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=sqlite:///./audioflow.db

# App Settings
DEBUG=False
APP_NAME=BooksMood

# File Storage  
UPLOAD_DIR=./app/static/uploads
MAX_FILE_SIZE=104857600

# Server
HOST=0.0.0.0
PORT=8000

# Production URL
PRODUCTION_URL=https://app.booksmood.ru
```

### 2. Telegram Bot Setup

1. **Бот**: `@booksmoodbot`
2. **Домен Mini App**: `https://app.booksmood.ru`

#### Настройка Mini App в BotFather:

```
/setmenubutton
@booksmoodbot
📚 Открыть аудиокниги
https://app.booksmood.ru
```

#### Настройка Web App Domain:

```
/setdomain
@booksmoodbot
app.booksmood.ru
```

### 3. Nginx конфигурация

```nginx
server {
    listen 80;
    server_name app.booksmood.ru;
    return 301 https://$server_name$request_uri;
}

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
        alias /path/to/booksmood/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4. Systemd сервис

Создайте `/etc/systemd/system/booksmood.service`:

```ini
[Unit]
Description=BooksMood AudioFlow API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/booksmood
Environment=PATH=/opt/booksmood/venv/bin
ExecStart=/opt/booksmood/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 5. Развертывание

```bash
# Клонирование репозитория
git clone https://github.com/Cossomoj/booksmood.git /opt/booksmood
cd /opt/booksmood

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
nano .env

# Инициализация базы данных
python scripts/init_db.py

# Создание директорий
mkdir -p app/static/uploads
chmod 755 app/static/uploads

# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable booksmood
sudo systemctl start booksmood
```

### 6. SSL сертификат

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d app.booksmood.ru

# Автообновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Проверка

После развертывания проверьте:

- ✅ **API**: https://app.booksmood.ru/health
- ✅ **Админ**: https://app.booksmood.ru/admin/login  
- ✅ **Docs**: https://app.booksmood.ru/docs
- ✅ **Bot**: https://t.me/booksmoodbot

### 8. Администрирование

**Первый вход в админ панель:**
- Логин: `admin`
- Пароль: `admin123`

⚠️ **ОБЯЗАТЕЛЬНО смените пароль после первого входа!**

### 9. Мониторинг

```bash
# Статус сервиса
sudo systemctl status booksmood

# Логи
sudo journalctl -u booksmood -f

# Производительность
htop
```

### 10. Обновление

```bash
cd /opt/booksmood
git pull origin master
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart booksmood
``` 