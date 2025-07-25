# 🚀 BooksMood - Запуск одной командой

## Мгновенный запуск

```bash
sudo docker-compose up --build -d
```

**Готово!** 🎉

- 🌐 **Сайт**: http://localhost
- 📚 **API**: http://localhost:8000
- ⚙️ **Админ**: http://localhost/admin/login
- 📖 **Документация**: http://localhost:8000/docs

## Данные для входа

**Админ панель:**
- Логин: `admin`
- Пароль: `admin123`

## Полезные команды

```bash
# Просмотр логов
sudo docker-compose logs -f

# Остановка
sudo docker-compose down

# Статус
sudo docker-compose ps

# Проверка здоровья
curl http://localhost/health
```

## Что включено

- ✅ **FastAPI** сервер на порту 8000
- ✅ **Nginx** прокси на порту 80
- ✅ **SQLite** база данных с данными по умолчанию
- ✅ **Telegram Bot** готов к настройке
- ✅ **Автоматический рестарт** контейнеров
- ✅ **Постоянное хранение** данных и файлов

## Настройка Telegram бота

После запуска настройте бота у **@BotFather**:

```
/setmenubutton
@booksmoodbot
📚 Открыть аудиокниги
http://ваш-домен
```

🎧 **Готово к использованию!** 