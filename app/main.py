from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os

from .config import settings
from .database import engine
from .models import Base
from .routers import auth, books, categories, users, admin
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

# Подключение роутеров
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)
app.include_router(users.router)
app.include_router(admin.router)

# Jinja2 шаблоны для админ панели
templates = Jinja2Templates(directory="app/admin/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница приложения"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AudioFlow - Telegram Mini App</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 40px 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .container {
                max-width: 600px;
            }
            h1 {
                font-size: 48px;
                margin-bottom: 20px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            .subtitle {
                font-size: 24px;
                margin-bottom: 40px;
                opacity: 0.9;
            }
            .emoji {
                font-size: 80px;
                margin-bottom: 30px;
            }
            .links {
                display: flex;
                gap: 20px;
                justify-content: center;
                flex-wrap: wrap;
            }
            .link {
                background: rgba(255,255,255,0.2);
                padding: 15px 30px;
                border-radius: 25px;
                text-decoration: none;
                color: white;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }
            .link:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">🎧</div>
            <h1>AudioFlow</h1>
            <p class="subtitle">Telegram Mini App для прослушивания аудиокниг</p>
            <div class="links">
                <a href="/docs" class="link">📚 API Документация</a>
                <a href="/admin/dashboard" class="link">⚙️ Админ панель</a>
                <a href="https://t.me/booksmoodbot" class="link">🤖 Открыть в Telegram</a>
            </div>
        </div>
    </body>
    </html>
    """)

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