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
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>AudioFlow - Telegram Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
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
        }}

        /* Telegram Web App адаптивные цвета */
        body.tg-theme {{
            --dark-bg: var(--tg-theme-bg-color, #0f0f0f);
            --card-bg: var(--tg-theme-secondary-bg-color, #1a1a1a);
            --text-primary: var(--tg-theme-text-color, #ffffff);
            --text-secondary: var(--tg-theme-hint-color, #a1a1aa);
            --primary: var(--tg-theme-button-color, #6366f1);
            --primary-dark: var(--tg-theme-button-color, #4f46e5);
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            overflow-x: hidden;
            position: relative;
            min-height: 100vh;
            padding-bottom: env(safe-area-inset-bottom);
        }}

        /* Анимированный фон */
        .animated-bg {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, var(--dark-bg) 0%, #1a0f2e 100%);
            z-index: -1;
        }}

        .animated-bg::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
            animation: rotate 30s linear infinite;
        }}

        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        /* Навигация */
        .app-header {{
            position: sticky;
            top: 0;
            background: rgba(15, 15, 15, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            z-index: 100;
            padding: 16px;
            padding-top: max(16px, env(safe-area-inset-top));
        }}

        .header-content {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 500px;
            margin: 0 auto;
        }}

        .app-logo {{
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .header-actions {{
            display: flex;
            gap: 12px;
        }}

        .icon-btn {{
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
        }}

        .icon-btn:hover {{
            background: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(99, 102, 241, 0.3);
        }}

        /* Контейнер приложения */
        .app-container {{
            max-width: 500px;
            margin: 0 auto;
            padding: 0 16px 80px;
            position: relative;
        }}

        /* Поиск */
        .search-section {{
            margin: 20px 0;
            position: relative;
        }}

        .search-input {{
            width: 100%;
            padding: 16px 50px 16px 20px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            color: var(--text-primary);
            font-size: 16px;
            transition: all 0.3s ease;
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}

        .search-icon {{
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }}

        /* Категории */
        .categories {{
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 16px 0;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }}

        .categories::-webkit-scrollbar {{
            display: none;
        }}

        .category-chip {{
            padding: 8px 20px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 24px;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            font-weight: 500;
        }}

        .category-chip.active {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-color: transparent;
            transform: scale(1.05);
        }}

        .category-chip:hover {{
            transform: translateY(-2px);
        }}

        /* Секции */
        .section {{
            margin: 32px 0;
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 600;
        }}

        .section-link {{
            color: var(--primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: gap 0.3s ease;
        }}

        .section-link:hover {{
            gap: 8px;
        }}

        /* Карточки книг */
        .books-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}

        .book-card {{
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .book-card:hover {{
            transform: translateY(-8px);
        }}

        .book-cover {{
            width: 100%;
            aspect-ratio: 3/4;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }}

        .book-cover img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .book-badge {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: var(--accent);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}

        .book-info {{
            margin-top: 8px;
        }}

        .book-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .book-author {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }}

        /* Горизонтальный скролл */
        .books-scroll {{
            display: flex;
            gap: 16px;
            overflow-x: auto;
            padding: 4px 0 16px;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }}

        .books-scroll::-webkit-scrollbar {{
            display: none;
        }}

        .book-card-horizontal {{
            flex: 0 0 140px;
        }}

        /* Большие карточки */
        .featured-card {{
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
        }}

        .featured-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, transparent 0%, rgba(99, 102, 241, 0.1) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .featured-card:hover::before {{
            opacity: 1;
        }}

        .featured-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(99, 102, 241, 0.2);
        }}

        .featured-cover {{
            width: 100px;
            height: 150px;
            border-radius: 12px;
            overflow: hidden;
            flex-shrink: 0;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }}

        .featured-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .featured-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .featured-author {{
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 12px;
        }}

        .featured-stats {{
            display: flex;
            gap: 16px;
            font-size: 14px;
            color: var(--text-secondary);
        }}

        .stat-item {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        /* Нижняя навигация */
        .bottom-nav {{
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
        }}

        .nav-item {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-secondary);
        }}

        .nav-item.active {{
            color: var(--primary);
        }}

        .nav-item:hover {{
            color: var(--primary);
        }}

        .nav-icon {{
            font-size: 24px;
        }}

        .nav-label {{
            font-size: 12px;
            font-weight: 500;
        }}

        /* Анимации */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .fade-in-up {{
            animation: fadeInUp 0.6s ease forwards;
        }}

        .admin-link {{
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
        }}

        .admin-link:hover {{
            background: var(--primary);
            color: white;
        }}

        /* Аудиоплеер */
        .audio-player {{
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
        }}

        .audio-player.show {{
            transform: translateY(0);
        }}

        .player-content {{
            max-width: 480px;
            margin: 0 auto;
        }}

        .player-book-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }}

        .player-cover {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: var(--card-bg);
            background-size: cover;
            background-position: center;
            flex-shrink: 0;
        }}

        .player-text {{
            flex: 1;
            min-width: 0;
        }}

        .player-title {{
            font-weight: 600;
            font-size: 14px;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .player-author {{
            font-size: 12px;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .player-controls {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 16px;
        }}

        .player-btn {{
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
        }}

        .player-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}

        .player-play-btn {{
            background: var(--primary);
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .player-play-btn:hover {{
            background: var(--primary-dark);
        }}

        .player-progress {{
            margin-bottom: 8px;
        }}

        .player-time {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}

        .progress-bar-container {{
            cursor: pointer;
            padding: 4px 0;
        }}

        .progress-bar {{
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: var(--primary);
            border-radius: 2px;
            transition: width 0.1s linear;
        }}

        /* Кнопка воспроизведения в карточке книги */
        .featured-play-btn {{
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
        }}

        .featured-play-btn:hover {{
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        }}

        /* Уведомления об ошибках */
        .error-notification {{
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
        }}

        @keyframes slideInDown {{
            from {{
                opacity: 0;
                transform: translateX(-50%) translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }}
        }}

        /* Обновляем карточки книг для кликабельности */
        .book-card {{
            cursor: pointer;
            transition: transform 0.2s ease;
        }}

        .book-card:hover {{
            transform: translateY(-4px);
        }}

        .book-card:active {{
            transform: translateY(-2px);
        }}
        /* Статус подключения Telegram */
        .telegram-status {{
            position: fixed;
            top: env(safe-area-inset-top, 10px);
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            z-index: 1001;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .telegram-status.show {{
            opacity: 1;
        }}

        .telegram-status.connected {{
            background: rgba(16, 185, 129, 0.8);
        }}

        .telegram-status.disconnected {{
            background: rgba(239, 68, 68, 0.8);
        }}

        /* Закладки в аудиоплеере */
        .bookmark-btn {{
            color: var(--primary) !important;
        }}

        .bookmark-btn:hover {{
            background: rgba(99, 102, 241, 0.1) !important;
        }}

        .bookmarks-list-btn.active {{
            background: var(--primary) !important;
            color: white !important;
        }}

        .bookmarks-panel {{
            margin-top: 16px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            animation: slideDown 0.3s ease;
        }}

        .bookmarks-header {{
            margin-bottom: 12px;
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .bookmarks-list {{
            max-height: 200px;
            overflow-y: auto;
        }}

        .bookmark-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .bookmark-item:last-child {{
            border-bottom: none;
        }}

        .bookmark-info {{
            flex: 1;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 8px;
            transition: background 0.2s ease;
        }}

        .bookmark-info:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}

        .bookmark-time {{
            font-size: 12px;
            color: var(--primary);
            font-weight: 600;
            margin-bottom: 2px;
        }}

        .bookmark-title {{
            font-size: 14px;
            color: var(--text-primary);
            margin-bottom: 2px;
        }}

        .bookmark-note {{
            font-size: 12px;
            color: var(--text-secondary);
            font-style: italic;
        }}

        .bookmark-delete-btn {{
            background: none;
            border: none;
            color: var(--text-secondary);
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            opacity: 0.7;
        }}

        .bookmark-delete-btn:hover {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            opacity: 1;
        }}

        /* Диалог создания закладки */
        .bookmark-dialog-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.3s ease;
        }}

        .bookmark-dialog {{
            background: var(--card-bg);
            border-radius: 16px;
            width: 90%;
            max-width: 400px;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            animation: slideUp 0.3s ease;
        }}

        .bookmark-dialog-header {{
            padding: 20px 20px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .bookmark-dialog-header h3 {{
            margin: 0;
            font-size: 18px;
            color: var(--text-primary);
        }}

        .dialog-close {{
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 24px;
            cursor: pointer;
            padding: 4px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }}

        .dialog-close:hover {{
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
        }}

        .bookmark-dialog-content {{
            padding: 20px;
        }}

        .bookmark-position {{
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            color: var(--text-primary);
            text-align: center;
        }}

        .form-group {{
            margin-bottom: 16px;
        }}

        .form-group label {{
            display: block;
            margin-bottom: 6px;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
        }}

        .form-group input,
        .form-group textarea {{
            width: 100%;
            padding: 12px;
            background: var(--dark-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.3s ease;
        }}

        .form-group input:focus,
        .form-group textarea:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}

        .form-group textarea {{
            resize: vertical;
            min-height: 60px;
        }}

        .bookmark-dialog-actions {{
            padding: 16px 20px 20px;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }}

        .btn {{
            padding: 10px 20px;
            border-radius: 8px;
            border: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn-secondary {{
            background: var(--card-bg);
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}

        .btn-secondary:hover {{
            background: var(--border);
            color: var(--text-primary);
        }}

        .btn-primary {{
            background: var(--primary);
            color: white;
        }}

        .btn-primary:hover {{
            background: var(--primary-dark);
        }}

        /* Анимации для диалогов */
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes slideDown {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Рейтинги */
        .rating-btn {{
            color: #fbbf24 !important;
        }}

        .rating-btn.rated {{
            background: rgba(251, 191, 36, 0.2) !important;
            color: #fbbf24 !important;
        }}

        .rating-btn:hover {{
            background: rgba(251, 191, 36, 0.1) !important;
        }}

        .book-actions {{
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .book-card:hover .book-actions {{
            opacity: 1;
        }}

        /* Диалог рейтинга */
        .rating-dialog-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.3s ease;
        }}

        .rating-dialog {{
            background: var(--card-bg);
            border-radius: 16px;
            width: 90%;
            max-width: 400px;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            animation: slideUp 0.3s ease;
        }}

        .rating-dialog-header {{
            padding: 20px 20px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .rating-dialog-header h3 {{
            margin: 0;
            font-size: 18px;
            color: var(--text-primary);
        }}

        .rating-dialog-content {{
            padding: 20px;
        }}

        .rating-stars-container {{
            text-align: center;
            margin-bottom: 20px;
        }}

        .rating-stars {{
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 12px;
        }}

        .rating-stars .star {{
            font-size: 32px;
            cursor: pointer;
            opacity: 0.3;
            transition: all 0.2s ease;
            user-select: none;
        }}

        .rating-stars .star:hover {{
            opacity: 0.8;
            transform: scale(1.1);
        }}

        .rating-text {{
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
        }}

        .rating-dialog-actions {{
            padding: 16px 20px 20px;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }}

        /* Остальные стили... */
    </style>
</head>
<body>
    <div class="animated-bg"></div>
    
    <!-- Статус подключения Telegram -->
    <div id="telegramStatus" class="telegram-status">
        <span id="statusText">Подключение...</span>
    </div>

    <!-- Ссылка на админ панель -->
    <a href="{settings.host}:{settings.port}/admin/dashboard" class="admin-link">⚙️ Админ</a>

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
            </div>

            <!-- Рекомендации дня -->
            <section class="section fade-in-up">
                <div class="section-header">
                    <h2 class="section-title">Книга дня</h2>
                </div>
                <div class="featured-card">
                    <div class="featured-cover"></div>
                    <div class="featured-content">
                        <h3 class="featured-title">Загрузка...</h3>
                        <p class="featured-author">Подождите...</p>
                    </div>
                </div>
            </section>

            <!-- Продолжить слушать -->
            <section class="section fade-in-up">
                <div class="section-header">
                    <h2 class="section-title">Продолжить слушать</h2>
                </div>
                <div class="books-scroll">
                    <p style="color: var(--text-secondary); text-align: center; padding: 20px;">Загрузка...</p>
                </div>
            </section>

            <!-- Популярные книги -->
            <section class="section fade-in-up">
                <div class="section-header">
                    <h2 class="section-title">Популярные</h2>
                </div>
                <div class="books-grid" id="popularBooks">
                    <p style="color: var(--text-secondary); text-align: center; padding: 40px; grid-column: 1 / -1;">Загрузка...</p>
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

    <script src="/static/audioflow.js"></script>
    <script>
        // Инициализация Telegram Web App
        const tg = window.Telegram?.WebApp;
        const statusEl = document.getElementById('telegramStatus');
        const statusText = document.getElementById('statusText');

        function updateTelegramStatus() {{
            if (tg) {{
                if (tg.initData) {{
                    statusText.textContent = 'Telegram ✓';
                    statusEl.className = 'telegram-status show connected';
                    document.body.classList.add('tg-theme');
                    
                    // Настройка темы
                    if (tg.colorScheme === 'dark') {{
                        document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#0f0f0f');
                        document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#ffffff');
                    }}
                }} else {{
                    statusText.textContent = 'Telegram (no data)';
                    statusEl.className = 'telegram-status show disconnected';
                }}
            }} else {{
                statusText.textContent = 'Веб-режим';
                statusEl.className = 'telegram-status show disconnected';
            }}

            // Скрываем статус через 3 секунды
            setTimeout(() => {{
                statusEl.classList.remove('show');
            }}, 3000);
        }}

        if (tg) {{
            tg.ready();
            tg.expand();
            
            // Настройки главной кнопки
            tg.MainButton.hide();
            
            // Настройки цветовой схемы
            if (tg.setHeaderColor) {{
                tg.setHeaderColor(tg.themeParams?.bg_color || '#0f0f0f');
            }}
        }}

        // Обновляем статус после загрузки
        document.addEventListener('DOMContentLoaded', updateTelegramStatus);

        // Инициализация AudioFlow приложения
        // audioFlow будет инициализирован из audioflow.js
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

    <script src="/static/audioflow.js"></script>
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
                        body: JSON.stringify({ username, password })
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