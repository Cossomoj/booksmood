# BooksMood - Скрипты Управления

Этот документ описывает использование скриптов для автоматической установки и удаления проекта BooksMood на сервере.

## 📦 Скрипт Установки (install.sh)

Автоматически устанавливает и запускает полный проект BooksMood на сервере.

### Что делает скрипт:
- ✅ Определяет операционную систему (Ubuntu/Debian/CentOS/RHEL/Rocky/AlmaLinux)
- ✅ Обновляет систему и устанавливает базовые зависимости
- ✅ Устанавливает Docker и Docker Compose
- ✅ Клонирует проект с GitHub
- ✅ Создает системного пользователя для проекта
- ✅ Генерирует безопасные пароли и конфигурацию
- ✅ Настраивает файрвол
- ✅ Запускает все сервисы в Docker контейнерах
- ✅ Создает systemd службу для автозапуска
- ✅ Инициализирует базу данных

### Использование:

```bash
# Полная установка на сервере
curl -sSL https://raw.githubusercontent.com/Cossomoj/booksmood/main/install.sh | bash

# Или загрузить и запустить локально
wget https://raw.githubusercontent.com/Cossomoj/booksmood/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

### После установки:

1. **Настройте Telegram Bot:**
   ```bash
   sudo nano /opt/booksmood/.env
   # Добавьте ваш TELEGRAM_BOT_TOKEN от @BotFather
   ```

2. **Перезапустите проект:**
   ```bash
   cd /opt/booksmood
   sudo docker-compose restart
   ```

3. **Проверьте доступность:**
   - Frontend: `http://YOUR_SERVER_IP:3000`
   - API: `http://YOUR_SERVER_IP:3001`
   - Admin Panel: `http://YOUR_SERVER_IP:3002`
   - MinIO Console: `http://YOUR_SERVER_IP:9001`

### Требования:
- Linux сервер (Ubuntu 18+, Debian 10+, CentOS 7+, RHEL 7+)
- Минимум 2GB RAM, 10GB свободного места
- Права sudo/root
- Интернет соединение

---

## 🗑️ Скрипт Удаления (uninstall.sh)

Полностью удаляет проект BooksMood и все связанные компоненты с сервера.

### Что делает скрипт:
- 🔴 Останавливает все контейнеры Docker
- 🔴 Удаляет все образы, volumes и сети проекта
- 🔴 Удаляет файлы проекта (/opt/booksmood)
- 🔴 Удаляет systemd службу
- 🔴 Удаляет системного пользователя
- 🔴 Очищает правила файрвола
- 🔴 Создает резервную копию .env файла
- 🔴 Опционально удаляет Docker

### Использование:

```bash
# Стандартная очистка с подтверждением
sudo ./uninstall.sh

# Принудительная очистка без подтверждения
sudo ./uninstall.sh --force

# Полная очистка включая Docker
sudo ./uninstall.sh --remove-docker

# Получить справку
./uninstall.sh --help
```

### ⚠️ ВНИМАНИЕ:
- Скрипт **безвозвратно удаляет** все данные проекта
- База данных и загруженные файлы будут **потеряны**
- Резервная копия .env сохраняется в `/tmp/`
- Docker остается в системе (если не указан `--remove-docker`)

---

## 🔧 Управление Проектом

### Проверка статуса:
```bash
cd /opt/booksmood
sudo docker-compose ps
```

### Просмотр логов:
```bash
cd /opt/booksmood
sudo docker-compose logs -f        # Все сервисы
sudo docker-compose logs backend   # Только backend
sudo docker-compose logs frontend  # Только frontend
```

### Перезапуск сервисов:
```bash
cd /opt/booksmood
sudo docker-compose restart        # Все сервисы
sudo docker-compose restart backend # Только backend
```

### Остановка/запуск:
```bash
cd /opt/booksmood
sudo docker-compose down           # Остановить
sudo docker-compose up -d          # Запустить
```

### Обновление проекта:
```bash
cd /opt/booksmood
git pull origin main
sudo docker-compose down
sudo docker-compose up -d --build
```

---

## 🚀 Быстрый Старт на Новом Сервере

### 1. Подключитесь к серверу:
```bash
ssh user@your-server-ip
```

### 2. Запустите установку:
```bash
curl -sSL https://raw.githubusercontent.com/Cossomoj/booksmood/main/install.sh | sudo bash
```

### 3. Дождитесь завершения установки (~5-10 минут)

### 4. Настройте Telegram Bot Token:
```bash
sudo nano /opt/booksmood/.env
# Найдите TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
# Замените YOUR_BOT_TOKEN_HERE на токен от @BotFather
```

### 5. Перезапустите проект:
```bash
cd /opt/booksmood
sudo docker-compose restart
```

### 6. Готово! Приложение доступно по адресам:
- **Frontend:** `http://your-server-ip:3000`
- **Admin Panel:** `http://your-server-ip:3002` (admin/admin123)

---

## 📋 Решение Проблем

### Проблема: Docker не запускается
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Проблема: Порты заняты
```bash
sudo netstat -tulpn | grep :3000
sudo lsof -i :3000
```

### Проблема: Нет места на диске
```bash
sudo docker system prune -a --volumes
sudo journalctl --vacuum-time=7d
```

### Проблема: Контейнеры не поднимаются
```bash
cd /opt/booksmood
sudo docker-compose down
sudo docker-compose up -d --force-recreate
sudo docker-compose logs
```

### Полная переустановка:
```bash
sudo ./uninstall.sh --force
sudo ./install.sh
```

---

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи: `sudo docker-compose logs`
2. Проверьте статус: `sudo docker-compose ps`
3. Перезапустите: `sudo docker-compose restart`
4. Создайте issue в репозитории GitHub

**Важные файлы:**
- Проект: `/opt/booksmood/`
- Конфигурация: `/opt/booksmood/.env`
- Логи: `sudo docker-compose logs`
- Служба: `sudo systemctl status booksmood` 