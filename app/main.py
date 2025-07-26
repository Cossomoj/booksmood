from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os

from .config import settings
from .database import engine
from .models import Base
from .routers import auth, books, categories, users, admin, upload
from .utils import ensure_directory_exists

# Создание таблиц БД
Base.metadata.create_all(bind=engine)

# Создание необходимых директорий
ensure_directory_exists(settings.upload_dir)
ensure_directory_exists(os.path.join(settings.upload_dir, "covers"))
ensure_directory_exists(os.path.join(settings.upload_dir, "audio"))
ensure_directory_exists("app/static")

app = FastAPI(
    title="AudioFlow API",
    description="Telegram Mini App для прослушивания аудиокниг",
    version="1.0.0",
    debug=settings.debug
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/static/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Подключение роутеров
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(upload.router)

# Jinja2 шаблоны для админ панели
templates = Jinja2Templates(directory="app/admin/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница приложения - Telegram Mini App"""
    return HTMLResponse("""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AudioFlow - Telegram Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --dark-bg: #0f0f0f;
            --card-bg: #1a1a1a;
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --border: #27272a;
            --success: #10b981;
            --warning: #f59e0b;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            overflow-x: hidden;
            position: relative;
            min-height: 100vh;
        }

        /* Анимированный фон */
        .animated-bg {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a0f2e 100%);
            z-index: -1;
        }

        .animated-bg::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
            animation: rotate 30s linear infinite;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Навигация */
        .app-header {
            position: sticky;
            top: 0;
            background: rgba(15, 15, 15, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            z-index: 100;
            padding: 16px;
        }

        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 500px;
            margin: 0 auto;
        }

        .app-logo {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-actions {
            display: flex;
            gap: 12px;
        }

        .icon-btn {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-primary);
        }

        .icon-btn:hover {
            background: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(99, 102, 241, 0.3);
        }

        /* Контейнер приложения */
        .app-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 0 16px 80px;
            position: relative;
        }

        /* Поиск */
        .search-section {
            margin: 20px 0;
            position: relative;
        }

        .search-input {
            width: 100%;
            padding: 16px 50px 16px 20px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            color: var(--text-primary);
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .search-icon {
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }

        /* Категории */
        .categories {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 16px 0;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }

        .categories::-webkit-scrollbar {
            display: none;
        }

        .category-chip {
            padding: 8px 20px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 24px;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            font-weight: 500;
        }

        .category-chip.active {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-color: transparent;
            transform: scale(1.05);
        }

        .category-chip:hover {
            transform: translateY(-2px);
        }

        /* Секции */
        .section {
            margin: 32px 0;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .section-title {
            font-size: 20px;
            font-weight: 600;
        }

        .section-link {
            color: var(--primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: gap 0.3s ease;
        }

        .section-link:hover {
            gap: 8px;
        }

        /* Карточки книг */
        .books-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }

        .book-card {
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .book-card:hover {
            transform: translateY(-8px);
        }

        .book-cover {
            width: 100%;
            aspect-ratio: 3/4;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        .book-cover img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .book-badge {
            position: absolute;
            top: 8px;
            right: 8px;
            background: var(--accent);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }

        .book-info {
            margin-top: 8px;
        }

        .book-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .book-author {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        /* Горизонтальный скролл */
        .books-scroll {
            display: flex;
            gap: 16px;
            overflow-x: auto;
            padding: 4px 0 16px;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }

        .books-scroll::-webkit-scrollbar {
            display: none;
        }

        .book-card-horizontal {
            flex: 0 0 140px;
        }

        /* Большие карточки */
        .featured-card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            gap: 20px;
            margin-bottom: 16px;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .featured-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, transparent 0%, rgba(99, 102, 241, 0.1) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .featured-card:hover::before {
            opacity: 1;
        }

        .featured-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(99, 102, 241, 0.2);
        }

        .featured-cover {
            width: 100px;
            height: 150px;
            border-radius: 12px;
            overflow: hidden;
            flex-shrink: 0;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }

        .featured-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .featured-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .featured-author {
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 12px;
        }

        .featured-stats {
            display: flex;
            gap: 16px;
            font-size: 14px;
            color: var(--text-secondary);
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Нижняя навигация */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 26, 0.98);
            backdrop-filter: blur(20px);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            padding: 8px 0;
            z-index: 100;
        }

        .nav-item {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-secondary);
        }

        .nav-item.active {
            color: var(--primary);
        }

        .nav-item:hover {
            color: var(--primary);
        }

        .nav-icon {
            font-size: 24px;
        }

        .nav-label {
            font-size: 12px;
            font-weight: 500;
        }

        /* Анимации */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease forwards;
        }

        .admin-link {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 15px;
            border-radius: 20px;
            text-decoration: none;
            color: var(--text-secondary);
            font-size: 12px;
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .admin-link:hover {
            background: var(--primary);
            color: white;
        }

        /* Аудиоплеер */
        .audio-player {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 26, 0.95);
            backdrop-filter: blur(20px);
            border-top: 1px solid var(--border);
            padding: 16px;
            transform: translateY(100%);
            transition: transform 0.3s ease;
            z-index: 1000;
        }

        .audio-player.show {
            transform: translateY(0);
        }

        .player-content {
            max-width: 480px;
            margin: 0 auto;
        }

        .player-book-info {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }

        .player-cover {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: var(--card-bg);
            background-size: cover;
            background-position: center;
            flex-shrink: 0;
        }

        .player-text {
            flex: 1;
            min-width: 0;
        }

        .player-title {
            font-weight: 600;
            font-size: 14px;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .player-author {
            font-size: 12px;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .player-controls {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 16px;
        }

        .player-btn {
            background: none;
            border: none;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 8px;
            border-radius: 50%;
            transition: all 0.2s ease;
            font-size: 12px;
        }

        .player-btn:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .player-play-btn {
            background: var(--primary);
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .player-play-btn:hover {
            background: var(--primary-dark);
        }

        .player-progress {
            margin-bottom: 8px;
        }

        .player-time {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .progress-bar-container {
            cursor: pointer;
            padding: 4px 0;
        }

        .progress-bar {
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--primary);
            border-radius: 2px;
            transition: width 0.1s linear;
        }

        /* Кнопка воспроизведения в карточке книги */
        .featured-play-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 16px;
            font-size: 14px;
        }

        .featured-play-btn:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        }

        /* Уведомления об ошибках */
        .error-notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--accent);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 9999;
            animation: slideInDown 0.3s ease;
        }

        @keyframes slideInDown {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }

        /* Обновляем карточки книг для кликабельности */
        .book-card {
            cursor: pointer;
            transition: transform 0.2s ease;
        }

        .book-card:hover {
            transform: translateY(-4px);
        }

        .book-card:active {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="animated-bg"></div>

    <!-- Ссылка на админ панель -->
    <a href="http://213.171.25.85:8088/admin/dashboard" class="admin-link">⚙️ Админ</a>

    <!-- Главная страница -->
    <div id="homePage" class="page active">
        <header class="app-header">
            <div class="header-content">
                <div class="app-logo">
                    <span>🎧</span>
                    <span>AudioFlow</span>
                </div>
                <div class="header-actions">
                    <button class="icon-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                    </button>
                    <button class="icon-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </header>

        <div class="app-container">
            <!-- Поиск -->
            <div class="search-section">
                <input type="text" class="search-input" placeholder="Поиск книг, авторов, жанров...">
                <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                </svg>
            </div>

            <!-- Категории -->
            <div class="categories">
                <div class="category-chip active">Все</div>
                <div class="category-chip">🔥 Популярное</div>
                <div class="category-chip">📚 Классика</div>
                <div class="category-chip">🚀 Фантастика</div>
                <div class="category-chip">💼 Бизнес</div>
                <div class="category-chip">🧠 Психология</div>
                <div class="category-chip">🕵️ Детективы</div>
                <div class="category-chip">❤️ Романы</div>
            </div>

            <!-- Рекомендации дня -->
            <section class="section fade-in-up">
                <div class="section-header">
                    <h2 class="section-title">Книга дня</h2>
                </div>
                <div class="featured-card">
                    <div class="featured-cover"></div>
                    <div class="featured-content">
                        <h3 class="featured-title">Мастер и Маргарита</h3>
                        <p class="featured-author">Михаил Булгаков</p>
                        <p style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">
                            Один из самых загадочных романов XX века, сочетающий в себе философию, мистику и сатиру...
                        </p>
                        <div class="featured-stats">
                            <div class="stat-item">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                                </svg>
                                <span>Бесплатно</span>
                            </div>
                            <div class="stat-item">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <polyline points="12 6 12 12 16 14"></polyline>
                                </svg>
                                <span>16ч 32м</span>
                            </div>
                            <div class="stat-item">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
                                </svg>
                                <span>4.9</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Продолжить слушать -->
            <section class="section fade-in-up" style="animation-delay: 0.1s;">
                <div class="section-header">
                    <h2 class="section-title">Продолжить слушать</h2>
                    <a href="#" class="section-link">
                        Все
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </a>
                </div>
                <div class="books-scroll">
                    <div class="book-card book-card-horizontal">
                        <div class="book-cover">
                            <div class="book-badge">75%</div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">Атомные привычки</div>
                            <div class="book-author">Джеймс Клир</div>
                        </div>
                    </div>
                    <div class="book-card book-card-horizontal">
                        <div class="book-cover" style="background: linear-gradient(135deg, #f59e0b 0%, #ec4899 100%);">
                            <div class="book-badge">23%</div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">Думай и богатей</div>
                            <div class="book-author">Наполеон Хилл</div>
                        </div>
                    </div>
                    <div class="book-card book-card-horizontal">
                        <div class="book-cover" style="background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);">
                            <div class="book-badge">45%</div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">Сапиенс</div>
                            <div class="book-author">Юваль Харари</div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Новинки -->
            <section class="section fade-in-up" style="animation-delay: 0.2s;">
                <div class="section-header">
                    <h2 class="section-title">Новинки</h2>
                    <a href="#" class="section-link">
                        Все
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </a>
                </div>
                <div class="books-grid">
                    <div class="book-card">
                        <div class="book-cover" style="background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);">
                            <div class="book-badge">NEW</div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">Проект Хейл Мэри</div>
                            <div class="book-author">Энди Вейр</div>
                        </div>
                    </div>
                    <div class="book-card">
                        <div class="book-cover" style="background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);">
                            <div class="book-badge">NEW</div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">Клара и Солнце</div>
                            <div class="book-author">Кадзуо Исигуро</div>
                        </div>
                    </div>
                    <div class="book-card">
                        <div class="book-cover" style="background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);">
                            <div class="book-badge">NEW</div>
                        </div>
                        <div class="book-info">
                            <div class="book-title">Тревожные люди</div>
                            <div class="book-author">Фредрик Бакман</div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </div>

    <!-- Нижняя навигация -->
    <nav class="bottom-nav">
        <div class="nav-item active">
            <span class="nav-icon">🏠</span>
            <span class="nav-label">Главная</span>
        </div>
        <div class="nav-item">
            <span class="nav-icon">🔍</span>
            <span class="nav-label">Поиск</span>
        </div>
        <div class="nav-item">
            <span class="nav-icon">📚</span>
            <span class="nav-label">Библиотека</span>
        </div>
        <div class="nav-item">
            <span class="nav-icon">👤</span>
            <span class="nav-label">Профиль</span>
        </div>
    </nav>

    <script>
        // Инициализация Telegram Web App
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }

        // Анимация при скролле
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        document.querySelectorAll('.fade-in-up').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'all 0.6s ease';
            observer.observe(el);
        });

        // Обработка навигации
        document.querySelectorAll('.nav-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                if (tg?.HapticFeedback) {
                    tg.HapticFeedback.selectionChanged();
                }
            });
        });

        // Обработка категорий
        document.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                
                if (tg?.HapticFeedback) {
                    tg.HapticFeedback.selectionChanged();
                }
            });
        });
    </script>
</body>
</html>""")

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "ok",
        "service": "AudioFlow API",
        "version": "1.0.0"
    }

# Админ панель роуты
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Дашборд админ панели"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа в админ панель"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Вход в админ панель - AudioFlow</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .login-card {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                width: 100%;
                max-width: 400px;
            }
            
            .logo {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .logo h1 {
                color: #667eea;
                font-size: 32px;
                margin-bottom: 10px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 500;
            }
            
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 15px;
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .error {
                color: #e74c3c;
                text-align: center;
                margin-top: 15px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="logo">
                <h1>🎧 AudioFlow</h1>
                <p>Админ панель</p>
            </div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Имя пользователя</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Пароль</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn">Войти</button>
                
                <div class="error" id="error"></div>
            </form>
            </div>

        <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('error');
            
            try {
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('admin_token', data.access_token);
                    window.location.href = '/admin/dashboard';
                } else {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'Неверное имя пользователя или пароль';
                }
            } catch (error) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Ошибка подключения к серверу';
            }
        });
    </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port) 