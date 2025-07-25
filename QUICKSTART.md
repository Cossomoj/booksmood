# 🚀 Быстрый запуск AudioFlow

## Автоматический запуск (рекомендуется)

```bash
# Одной командой - создаст venv, установит зависимости и запустит сервер
python3 run.py
```

## Ручная установка

```bash
# 1. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Инициализация базы данных
python scripts/init_db.py

# 4. Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## После запуска

- 🌐 **Главная страница**: http://localhost:8000
- ⚙️ **Админ панель**: http://localhost:8000/admin/login (admin/admin123)
- 📚 **API документация**: http://localhost:8000/docs

## Telegram Bot

Ваш бот уже настроен с токеном: `8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY`

Для подключения к Telegram:
1. Найдите бота в @BotFather
2. Используйте `/setmenubutton` 
3. Укажите URL вашего сервера

**Готово! 🎉** 