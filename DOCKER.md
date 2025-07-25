# 🐳 Docker развертывание BooksMood

## 🚀 Быстрый старт

### Автоматическое развертывание:

```bash
# Клонирование репозитория
git clone https://github.com/Cossomoj/booksmood.git
cd booksmood

# Быстрый запуск
make quick-start

# ИЛИ вручную
docker-compose up -d --build
```

**Готово!** BooksMood доступен по адресу: http://localhost

## 📋 Предварительные требования

- **Docker** версия 20.10+
- **Docker Compose** версия 2.0+
- **Make** (опционально, для удобных команд)
- **Git** для клонирования репозитория

### Проверка установки:
```bash
docker --version
docker-compose --version
make --version
```

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────┐
│                Browser                      │
└─────────────────┬───────────────────────────┘
                  │ HTTP/HTTPS
┌─────────────────▼───────────────────────────┐
│              Nginx (80/443)                 │
│         Load Balancer + SSL                 │
└─────────────────┬───────────────────────────┘
                  │ Proxy
┌─────────────────▼───────────────────────────┐
│           BooksMood App (8000)              │
│    FastAPI + Uvicorn + Supervisor          │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        SQLite Database + Files              │
│     Persistent Docker Volumes              │
└─────────────────────────────────────────────┘
```

## 🛠️ Конфигурация

### Переменные окружения

Создайте файл `docker/.env` из примера:
```bash
cp docker/env.example docker/.env
nano docker/.env
```

**Основные настройки:**
```env
# Telegram Bot
BOT_TOKEN=ваш_токен_бота
TELEGRAM_BOT_USERNAME=booksmoodbot

# Security (ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ!)
SECRET_KEY=ваш_секретный_ключ_минимум_32_символа

# Домен (для продакшн)
PRODUCTION_URL=https://app.booksmood.ru
```

### Структура томов

```
booksmood_database/     # SQLite база данных
booksmood_files/        # Загруженные аудиокниги и обложки
booksmood_logs/         # Логи приложения и Nginx
```

## 📦 Команды Make

### Основные команды:
```bash
make help           # Список всех команд
make build          # Собрать образ
make up             # Запустить сервисы
make down           # Остановить сервисы
make restart        # Перезапустить
make logs           # Показать логи
```

### Разработка:
```bash
make dev            # Режим разработки
make shell          # Подключиться к контейнеру
make db             # Подключиться к базе данных
make test           # Запустить тесты
```

### Продакшн:
```bash
make prod           # Продакшн режим (с SSL)
make backup         # Создать бэкап БД
make restore DB=file.db  # Восстановить БД
make update         # Обновить из Git
```

### Мониторинг:
```bash
make status         # Статус контейнеров
make health         # Проверка здоровья
make info           # Информация о системе
```

## 🌍 Режимы развертывания

### 1. Разработка (по умолчанию)
```bash
docker-compose up -d
```
- HTTP на порту 80
- Прямой доступ к API на порту 8000
- Debug режим включен

### 2. Продакшн
```bash
docker-compose --profile production up -d
```
- HTTPS на порту 443
- Nginx с SSL сертификатами
- Оптимизации производительности

## 🔒 SSL сертификаты

### Автоматическая настройка Let's Encrypt:
```bash
# Внутри контейнера или на хосте
./scripts/ssl-setup.sh
```

### Ручная настройка:
1. Поместите сертификаты в `docker/ssl/`
2. Запустите продакшн режим:
```bash
make prod
```

## 📊 Мониторинг и логи

### Просмотр логов:
```bash
# Все логи
make logs

# Только API
make logs-api

# Логи Nginx (в продакшн режиме)
docker logs booksmood_nginx
```

### Проверка здоровья:
```bash
make health
# ИЛИ
curl http://localhost/health
curl http://localhost:8000/health
```

### Мониторинг ресурсов:
```bash
make info
docker stats booksmood_app
```

## 🔧 Обслуживание

### Обновление:
```bash
# Автоматическое обновление
make update

# Ручное обновление
git pull origin master
make full-restart
```

### Бэкапы:
```bash
# Создать бэкап
make backup

# Восстановить из бэкапа
make restore DB=backups/audioflow_20240725_120000.db
```

### Очистка:
```bash
# Очистить неиспользуемые ресурсы
make clean

# Полная очистка (УДАЛЯЕТ ВСЕ ДАННЫЕ!)
make clean-all
```

## 🐛 Устранение неполадок

### Проблема: Контейнер не запускается
```bash
# Проверить логи
make logs

# Проверить статус
make status

# Пересобрать образ
make build
```

### Проблема: База данных не инициализируется
```bash
# Подключиться к контейнеру
make shell

# Инициализировать вручную
cd /app && python scripts/init_db.py
```

### Проблема: Нет доступа к файлам
```bash
# Проверить права доступа
docker exec booksmood_app ls -la /app/app/static/uploads/

# Исправить права
docker exec booksmood_app chmod 755 /app/app/static/uploads/
```

### Проблема: SSL сертификат не работает
```bash
# Проверить сертификаты
docker exec booksmood_nginx ls -la /etc/nginx/ssl/

# Перезапустить Nginx
docker restart booksmood_nginx
```

## 📈 Масштабирование

### Горизонтальное масштабирование:
```yaml
# В docker-compose.yml
services:
  booksmood:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

### Вертикальное масштабирование:
```yaml
services:
  booksmood:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          memory: 1G
```

## 🔐 Безопасность

### Рекомендации:
1. **Измените SECRET_KEY** в продакшн
2. **Используйте HTTPS** с валидными сертификатами
3. **Ограничьте доступ** к админ панели по IP
4. **Регулярно обновляйте** образы
5. **Мониторьте** логи на подозрительную активность

### Безопасная конфигурация:
```env
# Продакшн настройки
DEBUG=false
SECRET_KEY=очень_длинный_случайный_ключ
CORS_ORIGINS=["https://web.telegram.org", "https://app.booksmood.ru"]
```

## 📞 Поддержка

### Полезные команды:
```bash
# Статус всей системы
make info

# Подключение к базе данных
make db

# Интерактивная оболочка
make shell

# Просмотр конфигурации
docker-compose config
```

### Логи для отладки:
```bash
# Подробные логи
docker-compose logs --details

# Логи с временными метками
docker-compose logs -t

# Следить за логами в реальном времени
docker-compose logs -f
```

## 🚀 Готовые сценарии

### Локальная разработка:
```bash
git clone https://github.com/Cossomoj/booksmood.git
cd booksmood
make quick-start
# Доступно на http://localhost
```

### Продакшн развертывание:
```bash
git clone https://github.com/Cossomoj/booksmood.git
cd booksmood
cp docker/env.example docker/.env
# Отредактируйте docker/.env
./scripts/ssl-setup.sh  # Настройка SSL
make prod
# Доступно на https://app.booksmood.ru
```

### Обновление продакшн:
```bash
cd booksmood
make backup  # Сначала бэкап!
make update  # Обновление
make health  # Проверка
```

🎉 **BooksMood готов к работе в Docker!** 