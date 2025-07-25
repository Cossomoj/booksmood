# 🎧 AudioFlow - Telegram Mini App для аудиокниг

AudioFlow - это современное Telegram Mini App для прослушивания аудиокниг с удобным интерфейсом и мощной админ панелью.

## 🌐 Продакшн

**🤖 Бот**: [@booksmoodbot](https://t.me/booksmoodbot)  
**🌍 URL**: https://app.booksmood.ru  
**⚙️ Админ**: https://app.booksmood.ru/admin/login

👉 **Полные инструкции по развертыванию**: [PRODUCTION.md](PRODUCTION.md)

## ✨ Особенности

- 🚀 **Telegram Web App** - работает прямо в Telegram без установки
- 🎵 **Аудиоплеер** - полнофункциональный плеер с сохранением прогресса
- 📚 **Большая библиотека** - поддержка категорий и поиска
- 👤 **Пользовательские профили** - история прослушивания и избранное
- ⚙️ **Админ панель** - управление контентом и пользователями
- 📱 **Адаптивный дизайн** - оптимизирован для мобильных устройств

## 🛠 Технологический стек

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **SQLite** - легковесная база данных
- **Pydantic** - валидация данных
- **JWT** - безопасная авторизация

### Frontend
- **HTML5/CSS3/JavaScript** - современные веб-технологии
- **Telegram Web App SDK** - интеграция с Telegram

## 📋 Требования

- Python 3.10+
- Telegram Bot (токен из @BotFather)

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd audioflow
```

### 2. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Telegram Bot (ваш токен уже настроен)
BOT_TOKEN=8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY
TELEGRAM_BOT_USERNAME=AudioFlowBot

# Security
SECRET_KEY=audioflow-secret-key-2024-very-secure-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=sqlite:///./audioflow.db

# App Settings
DEBUG=True
CORS_ORIGINS=["https://web.telegram.org", "http://localhost:3000"]

# File Storage
UPLOAD_DIR=./app/static/uploads
MAX_FILE_SIZE=104857600

# Server
HOST=0.0.0.0
PORT=8000
```

### 4. Инициализация базы данных

```bash
python scripts/init_db.py
```

Скрипт создаст:
- ✅ Все необходимые таблицы
- ✅ Категории по умолчанию (Классика, Фантастика, и др.)
- ✅ Администратора с логином `admin` и паролем `admin123`

### 5. Запуск сервера

```bash
# Для разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Для продакшена
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Настройка Telegram Bot

1. Откройте @BotFather в Telegram
2. Найдите вашего бота (токен уже настроен в коде)
3. Используйте команду `/setmenubutton`
4. Укажите URL: `https://your-domain.com` (или для разработки `https://your-ngrok-url.com`)

## 📱 Доступ к приложению

После запуска сервера доступны:

- **Главная страница**: http://localhost:8000
- **API документация**: http://localhost:8000/docs
- **Админ панель**: http://localhost:8000/admin/login
- **Telegram Mini App**: в вашем боте или https://t.me/YourBotUsername

## 🔐 Администрирование

### Вход в админ панель

1. Откройте http://localhost:8000/admin/login
2. Войдите с данными:
   - **Логин**: `admin`
   - **Пароль**: `admin123`
3. ⚠️ **Обязательно смените пароль в продакшене!**

### Возможности админ панели

- 📊 **Dashboard** - статистика и аналитика
- 📚 **Управление книгами** - добавление, редактирование, удаление
- 🏷️ **Категории** - управление жанрами
- 👥 **Пользователи** - просмотр активности пользователей
- 📁 **Файлы** - загрузка обложек и аудиофайлов

### Добавление книг

1. Войдите в админ панель
2. Перейдите в раздел "Книги"
3. Нажмите "Добавить книгу"
4. Заполните информацию:
   - Название и автор
   - Описание
   - Категория
   - Загрузите обложку (JPEG/PNG, до 5MB)
   - Загрузите аудиофайл (MP3, до 500MB)

## 🌐 API Эндпоинты

### Авторизация
- `POST /api/auth/telegram` - авторизация через Telegram Web App

### Книги
- `GET /api/books` - список книг
- `GET /api/books/{book_id}` - детали книги
- `GET /api/books/search` - поиск книг

### Пользователь
- `GET /api/user/library` - библиотека пользователя
- `POST /api/user/history/{book_id}` - обновить прогресс
- `POST /api/user/favorites/{book_id}` - добавить в избранное

### Админ панель
- `POST /api/admin/login` - вход администратора
- `GET /api/admin/dashboard` - статистика
- `POST /api/admin/books` - создание книги
- `PUT /api/admin/books/{book_id}` - редактирование
- `DELETE /api/admin/books/{book_id}` - удаление

Полная документация доступна по адресу `/docs`

## 📁 Структура проекта

```
audioflow/
├── app/                     # Основное приложение
│   ├── routers/            # API роутеры
│   ├── admin/              # Админ панель
│   ├── static/             # Статические файлы
│   ├── models.py           # Модели базы данных
│   ├── schemas.py          # Pydantic схемы
│   ├── auth.py             # Авторизация
│   ├── config.py           # Конфигурация
│   └── main.py             # Точка входа
├── scripts/                # Утилиты
│   └── init_db.py         # Инициализация БД
├── requirements.txt        # Зависимости Python
└── README.md              # Документация
```

## 🐳 Развертывание с Docker

```bash
# Сборка образа
docker build -t audioflow .

# Запуск контейнера
docker run -p 8000:8000 audioflow
```

## 🔧 Разработка

### Установка в режиме разработки

```bash
# Установка с возможностью редактирования
pip install -e .

# Запуск с автоперезагрузкой
uvicorn app.main:app --reload
```

### Тестирование

```bash
# Запуск тестов
pytest

# С покрытием кода
pytest --cov=app
```

### Линтинг

```bash
# Проверка кода
flake8 app/
black app/
isort app/
```

## 🚀 Продакшн

### Переменные окружения для продакшена

```env
DEBUG=False
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=sqlite:///./audioflow.db
CORS_ORIGINS=["https://web.telegram.org"]
```

### Развертывание на VPS

1. **Подготовка сервера**:
```bash
sudo apt update
sudo apt install python3.10 python3-pip nginx
```

2. **Установка приложения**:
```bash
cd /var/www/
sudo git clone <repository-url> audioflow
cd audioflow
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt
```

3. **Настройка systemd**:
```bash
sudo nano /etc/systemd/system/audioflow.service
```

4. **Настройка Nginx**:
```bash
sudo nano /etc/nginx/sites-available/audioflow
```

5. **SSL сертификат**:
```bash
sudo certbot --nginx -d your-domain.com
```

## 📞 Поддержка

- 📧 Email: support@audioflow.com
- 💬 Telegram: @AudioFlowSupport
- 🐛 Issues: GitHub Issues

## 📄 Лицензия

MIT License - подробности в файле LICENSE

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

**Сделано с ❤️ для любителей аудиокниг** 