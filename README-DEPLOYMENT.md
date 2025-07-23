# 🚀 Развертывание BooksMood на сервере

## 📋 Информация о сервере

- **Сервер**: `user1@213.171.25.85`
- **SSH ключ**: `~/.ssh/id_ed25519`
- **Репозиторий**: `git@github.com:Cossomoj/booksmood.git`
- **Директория развертывания**: `/opt/booksmood`

## 🎯 Быстрый старт

### 1. Автоматическое развертывание с локальной машины

```bash
# Запуск полного развертывания
./scripts/local-to-server.sh
```

### 2. Ручное развертывание через SSH

```bash
# Подключение к серверу
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85

# Запуск развертывания на сервере  
./scripts/server-deploy.sh deploy
```

### 3. GitHub Actions (автоматическое при push)

Настройте секреты в GitHub:
- `SERVER_SSH_KEY` - приватный SSH ключ
- `SERVER_HOST` - `213.171.25.85`
- `SERVER_USER` - `user1`
- `TELEGRAM_BOT_TOKEN` - токен вашего бота
- `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `JWT_SECRET`

## 📡 Доступные URL после развертывания

- **Frontend (MiniApp)**: http://213.171.25.85:3000
- **Admin Panel**: http://213.171.25.85:3002
- **Backend API**: http://213.171.25.85:3001
- **MinIO Console**: http://213.171.25.85:9001

## ⚙️ Конфигурация

### Обязательные настройки

После развертывания отредактируйте `.env.prod`:

```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85
nano /opt/booksmood/.env.prod
```

**Обязательно заполните:**
```env
TELEGRAM_BOT_TOKEN=your-real-bot-token-here
TELEGRAM_BOT_USERNAME=your_bot_username
```

**Перезапустите после изменений:**
```bash
cd /opt/booksmood
docker-compose -f docker-compose.prod.yml restart
```

### Получение Telegram Bot Token

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен
5. Настройте MiniApp URL: `http://213.171.25.85:3000`

## 🔧 Управление сервисами

### Основные команды

```bash
# Подключение к серверу
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85

# Переход в директорию проекта
cd /opt/booksmood

# Статус сервисов
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Перезапуск всех сервисов
docker-compose -f docker-compose.prod.yml restart

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.prod.yml restart backend
```

### Мониторинг

```bash
# Проверка здоровья API
curl http://localhost:3001/health

# Использование ресурсов
docker stats

# Логи ошибок
docker-compose -f docker-compose.prod.yml logs backend | grep ERROR
```

## 🔄 Обновление приложения

### Автоматическое (через Git push)

Просто сделайте push в main ветку - GitHub Actions автоматически развернет обновления.

### Ручное обновление

```bash
# Подключение к серверу
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85

# Обновление кода
cd /opt/booksmood
git pull origin main

# Пересборка и перезапуск
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Через скрипт

```bash
# С локальной машины
./scripts/local-to-server.sh

# На сервере
./scripts/server-deploy.sh update
```

## 🗄️ База данных

### Миграции

```bash
# Выполнение миграций
docker-compose -f docker-compose.prod.yml exec backend npx prisma migrate deploy

# Просмотр схемы
docker-compose -f docker-compose.prod.yml exec backend npx prisma db pull
```

### Backup

```bash
# Создание backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U booksmood booksmood > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U booksmood -d booksmood < backup_file.sql
```

## 🔒 Безопасность

### Firewall (рекомендуется)

```bash
# Настройка ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 3000  # Frontend
sudo ufw allow 3001  # API
sudo ufw allow 3002  # Admin
sudo ufw enable
```

### SSL сертификаты (для production)

```bash
# Установка certbot
sudo apt install certbot

# Получение сертификатов
sudo certbot certonly --standalone -d yourdomain.com

# Настройка nginx с SSL (см. nginx/nginx.conf)
```

## 🚨 Устранение неполадок

### Проблемы с подключением

```bash
# Проверка SSH
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "echo 'Подключение работает'"

# Проверка портов
telnet 213.171.25.85 3000
```

### Проблемы с Docker

```bash
# Очистка Docker
docker system prune -a -f

# Перестроение образов
docker-compose -f docker-compose.prod.yml build --no-cache --pull
```

### Проблемы с Git

```bash
# Проверка SSH ключей
ssh -T git@github.com

# Сброс репозитория
git reset --hard origin/main
```

### Логи отладки

```bash
# Подробные логи Docker
docker-compose -f docker-compose.prod.yml logs --tail=100 -f

# Логи системы
sudo journalctl -u docker.service -f

# Использование ресурсов
free -h
df -h
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь что все сервисы запущены: `docker-compose ps`
3. Проверьте доступность портов
4. Перезапустите сервисы: `docker-compose restart`

---

💡 **Совет**: Сохраните этот файл и команды для быстрого доступа к управлению сервером! 