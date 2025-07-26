# 🔐 Ручное управление SSL сертификатами для BooksMood

## 📋 Обзор

Теперь SSL сертификаты генерируются **вручную на VPS** и копируются в Docker контейнер при запуске. Сертификат не генерируется каждый раз автоматически.

## 🛠️ Первоначальная настройка

### 1. Скопируйте скрипт на VPS

```bash
# Подключаемся к VPS
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85

# Создаем папку для SSL
sudo mkdir -p /opt/ssl-certs

# Скачиваем скрипт генерации
curl -o /tmp/ssl-generate.sh https://raw.githubusercontent.com/Cossomoj/booksmood/master/ssl-generate.sh
sudo mv /tmp/ssl-generate.sh /opt/ssl-certs/
sudo chmod +x /opt/ssl-certs/ssl-generate.sh
```

### 2. Сгенерируйте SSL сертификат

```bash
# Запускаем генерацию SSL (только первый раз!)
cd /opt/ssl-certs
sudo bash ssl-generate.sh
```

Скрипт:
- ✅ Остановит Docker контейнеры 
- ✅ Установит certbot (если нужно)
- ✅ Сгенерирует SSL сертификат для `app.booksmood.ru`
- ✅ Сохранит сертификаты в `/opt/ssl-certs/`
- ✅ Создаст скрипт обновления `renew.sh`

### 3. Запустите Docker с SSL

```bash
cd /opt/booksmood
sudo docker-compose up --build -d
```

## 📁 Структура файлов на VPS

```
/opt/ssl-certs/
├── fullchain.pem      # Полная цепочка сертификатов
├── privkey.pem        # Приватный ключ
├── cert.pem           # Основной сертификат
├── chain.pem          # Цепочка CA
├── ssl-generate.sh    # Скрипт первоначальной генерации
├── renew.sh           # Скрипт обновления
├── config/            # Конфигурация certbot
├── work/              # Рабочие файлы
└── logs/              # Логи certbot
```

## 🔄 Обновление сертификата

SSL сертификаты от Let's Encrypt действуют **90 дней**. Для обновления:

```bash
# Подключаемся к VPS
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85

# Запускаем обновление
cd /opt/ssl-certs
sudo bash renew.sh
```

Скрипт `renew.sh`:
- ✅ Остановит Docker контейнеры
- ✅ Обновит сертификат
- ✅ Скопирует новые файлы
- ✅ Перезапустит Docker

## 🚀 Как это работает

### При запуске Docker контейнера:

1. **Монтирование**: `/opt/ssl-certs` → `/host-ssl` (read-only)
2. **Проверка**: Скрипт `check-ssl.sh` ищет сертификаты
3. **Копирование**: Если найдены → копирует в `/etc/nginx/ssl/`
4. **Nginx**: Автоматически использует HTTPS если сертификаты есть

### Режимы работы:

| Состояние | Поведение |
|-----------|-----------|
| 🚫 **Нет сертификатов** | HTTP only на `http://app.booksmood.ru` |
| ✅ **Есть сертификаты** | HTTPS на `https://app.booksmood.ru` + редирект HTTP→HTTPS |

## 📝 Команды для управления

### Просмотр статуса сертификата
```bash
# Проверка срока действия
sudo openssl x509 -in /opt/ssl-certs/fullchain.pem -text -noout | grep "Not After"

# Просмотр файлов
ls -la /opt/ssl-certs/*.pem
```

### Ручная остановка/запуск Docker
```bash
# Остановка
cd /opt/booksmood && sudo docker-compose down

# Запуск
cd /opt/booksmood && sudo docker-compose up -d
```

### Проверка логов SSL
```bash
# Логи проверки SSL в контейнере
sudo docker logs booksmood_app | grep ssl

# Логи nginx
sudo docker exec booksmood_app tail -f /var/log/nginx.log
```

## 🔧 Устранение неисправностей

### Проблема: HTTPS не работает

```bash
# 1. Проверьте наличие сертификатов на VPS
ls -la /opt/ssl-certs/*.pem

# 2. Перезапустите контейнер
cd /opt/booksmood && sudo docker-compose restart

# 3. Проверьте логи
sudo docker logs booksmood_app
```

### Проблема: Сертификат просрочен

```bash
# Принудительное обновление
cd /opt/ssl-certs
sudo certbot renew --force-renewal \
    --config-dir /opt/ssl-certs/config \
    --work-dir /opt/ssl-certs/work \
    --logs-dir /opt/ssl-certs/logs

# Скопируйте новые сертификаты
sudo bash renew.sh
```

## 🔗 Доступные адреса

- **Главная (HTTPS)**: https://app.booksmood.ru
- **Главная (HTTP)**: http://app.booksmood.ru (редирект на HTTPS)
- **Админ панель**: http://213.171.25.85:8088/admin/dashboard
- **API документация**: https://app.booksmood.ru/docs
- **Health check**: https://app.booksmood.ru/health

## ⚡ Автоматизация обновления

Можете настроить cron для автоматического обновления:

```bash
# Добавить в crontab
sudo crontab -e

# Добавить строку (обновление каждый месяц)
0 3 1 * * /opt/ssl-certs/renew.sh >> /var/log/ssl-renew.log 2>&1
```

## 🎯 Преимущества этого подхода

- ✅ **Контроль**: Вы полностью контролируете когда обновлять сертификат
- ✅ **Стабильность**: Нет риска поломки при автообновлении
- ✅ **Эффективность**: Контейнер стартует быстрее (нет генерации SSL)
- ✅ **Гибкость**: Можете использовать любые сертификаты (Let's Encrypt, платные)
- ✅ **Отладка**: Легче диагностировать проблемы 