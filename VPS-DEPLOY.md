# 🚀 BooksMood - Развертывание на VPS одной командой

## 📋 Что нужно на VPS

**Только один файл:** `docker-compose.yml`

## 🔧 Быстрая установка

### 1. Подключитесь к VPS:
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85
```

### 2. Установите Docker (если не установлен):
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогиньтесь для применения прав Docker
exit
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85
```

### 3. Создайте директорию и файл:
```bash
mkdir -p /opt/booksmood
cd /opt/booksmood
```

### 4. Создайте docker-compose.yml:
```bash
cat > docker-compose.yml << 'EOF'
services:
  # BooksMood основное приложение
  booksmood:
    build:
      context: https://github.com/Cossomoj/booksmood.git
      dockerfile: Dockerfile
    container_name: booksmood_app
    ports:
      - "80:80"      # Nginx
      - "8000:8000"  # FastAPI (для прямого доступа)
    volumes:
      # Постоянное хранение базы данных
      - booksmood_data:/app/audioflow.db
      # Постоянное хранение загруженных файлов
      - booksmood_uploads:/app/app/static/uploads
      # Логи
      - booksmood_logs:/var/log
    environment:
      # Telegram Bot
      - BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY
      - TELEGRAM_BOT_USERNAME=booksmoodbot
      
      # Security (ВАЖНО: измените в продакшн!)
      - SECRET_KEY=booksmood-production-secret-key-2024-CHANGE-THIS-IN-PRODUCTION
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=10080
      
      # Database
      - DATABASE_URL=sqlite:///./audioflow.db
      
      # App Settings
      - DEBUG=false
      - APP_NAME=BooksMood
      - HOST=0.0.0.0
      - PORT=8000
      
      # File Storage
      - UPLOAD_DIR=./app/static/uploads
      - MAX_FILE_SIZE=104857600
      
      # CORS Origins (добавьте ваш IP/домен)
      - CORS_ORIGINS=["https://web.telegram.org", "https://app.booksmood.ru", "http://213.171.25.85", "http://localhost"]
      
      # Production
      - PRODUCTION_URL=https://app.booksmood.ru
      
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - booksmood_network
    labels:
      - "com.booksmood.service=api"
      - "com.booksmood.version=1.0"
      - "com.booksmood.description=BooksMood AudioFlow - Telegram Mini App для аудиокниг"

# Сети
networks:
  booksmood_network:
    driver: bridge
    name: booksmood_net

# Тома для постоянного хранения
volumes:
  booksmood_data:
    name: booksmood_database
    driver: local
  booksmood_uploads:
    name: booksmood_files
    driver: local
  booksmood_logs:
    name: booksmood_logs
    driver: local
EOF
```

### 5. 🚀 Запуск одной командой:
```bash
sudo docker-compose up --build -d
```

**Готово!** 🎉

## 🌐 Результат

После запуска BooksMood будет доступен по адресам:

- **🌐 Сайт**: http://213.171.25.85
- **📚 API**: http://213.171.25.85:8000
- **⚙️ Админ**: http://213.171.25.85/admin/login
- **📖 Docs**: http://213.171.25.85:8000/docs

**Админ доступ:** `admin` / `admin123`

## 📊 Управление

```bash
# Просмотр логов
sudo docker-compose logs -f

# Просмотр статуса
sudo docker-compose ps

# Перезапуск
sudo docker-compose restart

# Остановка
sudo docker-compose down

# Проверка здоровья
curl http://localhost/health
```

## 🔄 Обновление

Для получения последней версии:
```bash
sudo docker-compose down
sudo docker-compose pull
sudo docker-compose up --build -d
```

## ⚙️ Настройка для вашего домена

Если у вас есть домен, отредактируйте в docker-compose.yml:

```yaml
environment:
  # Замените на ваш домен
  - CORS_ORIGINS=["https://web.telegram.org", "https://ваш-домен.com"]
  - PRODUCTION_URL=https://ваш-домен.com
```

## 🔒 Безопасность

**ОБЯЗАТЕЛЬНО измените в продакшн:**

```yaml
environment:
  - SECRET_KEY=ваш-очень-длинный-секретный-ключ-минимум-32-символа
```

## 🎯 Что происходит при запуске

1. **Docker скачивает** последний код из GitHub
2. **Собирает образ** с FastAPI + Nginx
3. **Создает тома** для постоянного хранения данных
4. **Инициализирует базу данных** с категориями и админом
5. **Запускает сервисы** с автоматическим перезапуском

## 🆘 Устранение проблем

### Проблема: Порт занят
```bash
sudo netstat -tlnp | grep :80
sudo docker ps
sudo docker-compose down
```

### Проблема: Docker нет прав
```bash
sudo usermod -aG docker $USER
# Перелогиньтесь
```

### Проблема: Не работает API
```bash
sudo docker-compose logs booksmood
curl http://localhost:8000/health
```

🎉 **BooksMood готов к использованию!** 