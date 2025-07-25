# 🔐 HTTPS Setup для app.booksmood.ru

## 🚀 Быстрый запуск (одна команда)

```bash
./deploy-ssl.sh
```

Этот скрипт автоматически:
- ✅ Проверит DNS запись app.booksmood.ru
- 🛑 Остановит старые контейнеры
- 🔨 Создаст SSL-конфигурацию на VPS
- 📦 Соберет и запустит новый контейнер
- 🔐 Получит SSL сертификат от Let's Encrypt
- 🧪 Протестирует доступность

## 📋 Пошаговая инструкция

### 1. Проверка DNS
```bash
dig +short app.booksmood.ru
# Должно вернуть: 213.171.25.85
```

### 2. Остановка старых контейнеров
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "cd /opt/booksmood && sudo docker-compose down"
```

### 3. Развертывание SSL версии
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85
sudo mkdir -p /opt/booksmood-ssl
cd /opt/booksmood-ssl

# Скачивание конфигурации
wget https://raw.githubusercontent.com/Cossomoj/booksmood/main/docker-compose.ssl.yml -O docker-compose.yml

# Запуск
sudo docker-compose up --build -d
```

### 4. Мониторинг процесса
```bash
# Логи сборки
sudo docker-compose logs -f

# Логи SSL setup
sudo docker-compose logs booksmood | grep -i ssl

# Статус контейнера
sudo docker-compose ps
```

## 🔧 Конфигурация

### Dockerfile.ssl особенности:
- ✅ **Certbot**: Автоматическое получение SSL сертификатов
- ✅ **Nginx**: Настроен для HTTP → HTTPS редиректа
- ✅ **Cron**: Автообновление сертификатов
- ✅ **Supervisor**: Управление всеми процессами

### Docker Compose SSL:
- ✅ **Порты**: 80 (HTTP), 443 (HTTPS), 8000 (API)
- ✅ **Volumes**: Персистентное хранение SSL сертификатов
- ✅ **Environment**: HTTPS-ready настройки

## 🌐 Результат

После успешного развертывания доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| **Основной сайт** | https://app.booksmood.ru | Telegram Mini App |
| **API Документация** | https://app.booksmood.ru:8000/docs | FastAPI Swagger |
| **Админ панель** | https://app.booksmood.ru/admin/login | Админка (admin/admin123) |
| **Health Check** | https://app.booksmood.ru/health | Проверка статуса |

## 🛠️ Команды управления

### Перезапуск контейнера:
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "cd /opt/booksmood-ssl && sudo docker-compose restart"
```

### Просмотр логов:
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "cd /opt/booksmood-ssl && sudo docker-compose logs -f"
```

### Проверка SSL сертификата:
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "sudo docker exec booksmood_ssl_app certbot certificates"
```

### Обновление SSL сертификата:
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "sudo docker exec booksmood_ssl_app certbot renew"
```

## 🔍 Диагностика

### Проверка SSL сертификата:
```bash
curl -I https://app.booksmood.ru
openssl s_client -connect app.booksmood.ru:443 -servername app.booksmood.ru
```

### Проверка редиректа HTTP → HTTPS:
```bash
curl -I http://app.booksmood.ru
```

### Тест API:
```bash
curl https://app.booksmood.ru/health
curl https://app.booksmood.ru:8000/docs
```

## ⚠️ Troubleshooting

### SSL сертификат не получен:
1. Проверьте DNS: `dig app.booksmood.ru`
2. Проверьте доступность порта 80: `nc -zv app.booksmood.ru 80`
3. Посмотрите логи: `sudo docker-compose logs booksmood | grep -i error`

### HTTPS не работает:
1. Проверьте статус контейнера: `sudo docker-compose ps`
2. Проверьте порт 443: `sudo ufw status | grep 443`
3. Перезапустите: `sudo docker-compose restart`

### Telegram Mini App не работает:
1. Убедитесь что CORS включает `https://web.telegram.org`
2. Проверьте переменную `PRODUCTION_URL=https://app.booksmood.ru`
3. Обновите URL в @BotFather для вашего бота

## 📱 Telegram Bot Setup

После развертывания обновите URL Mini App в @BotFather:

1. Откройте @BotFather в Telegram
2. Выберите команду `/mybots`
3. Выберите вашего бота `@booksmoodbot`
4. Нажмите `Bot Settings` → `Menu Button`
5. Измените URL на: `https://app.booksmood.ru`

## 🎯 Автоматическое обновление

SSL сертификаты обновляются автоматически через cron каждый день в 12:00.

Для проверки автообновления:
```bash
ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85 "sudo docker exec booksmood_ssl_app crontab -l"
```

## 🔐 Безопасность

- ✅ **SSL/TLS**: Современные шифры и протоколы
- ✅ **HSTS**: Принудительное использование HTTPS
- ✅ **Security Headers**: Защита от XSS, CSRF
- ✅ **Rate Limiting**: Защита от DDoS
- ✅ **Auto-Renewal**: Автоматическое обновление сертификатов

---

**✅ После выполнения этих шагов ваш сервис будет доступен по адресу: https://app.booksmood.ru** 