from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from passlib.context import CryptContext
from datetime import datetime
from typing import List, Optional

from ..database import get_db
from ..schemas import (
    AdminLogin, AdminToken, AdminResponse, DashboardResponse, DashboardStats,
    BookCreate, BookUpdate, BookResponse, CategoryCreate, CategoryResponse,
    StatusResponse, UserResponse
)
from ..models import Admin, User, Book, Category, ListeningHistory
from ..dependencies import get_current_admin, get_superadmin
from ..auth import create_admin_token
from ..utils import save_and_optimize_image, save_audio_file, delete_file
from ..config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/login", response_model=AdminToken)
async def admin_login(
    credentials: AdminLogin,
    db: Session = Depends(get_db)
):
    """Авторизация администратора"""
    
    admin = db.query(Admin).filter(
        Admin.username == credentials.username,
        Admin.is_active == True
    ).first()
    
    if not admin or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Обновляем время последнего входа
    admin.last_login = datetime.utcnow()
    db.commit()
    
    token = create_admin_token(admin.id)
    
    return AdminToken(
        access_token=token,
        token_type="bearer",
        admin=AdminResponse.model_validate(admin)
    )

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Получение данных для дашборда"""
    
    # Статистика
    total_users = db.query(User).count()
    total_books = db.query(Book).filter(Book.is_active == True).count()
    total_plays = db.query(func.sum(ListeningHistory.play_count)).scalar() or 0
    
    # Новые пользователи сегодня
    today = datetime.utcnow().date()
    new_users_today = db.query(User).filter(
        func.date(User.created_at) == today
    ).count()
    
    stats = DashboardStats(
        total_users=total_users,
        total_books=total_books,
        total_plays=total_plays,
        new_users_today=new_users_today
    )
    
    # Последние книги
    recent_books = db.query(Book).filter(
        Book.is_active == True
    ).order_by(desc(Book.created_at)).limit(5).all()
    
    # Популярные книги
    popular_books = db.query(Book).filter(
        Book.is_active == True
    ).order_by(desc(Book.plays_count)).limit(5).all()
    
    return DashboardResponse(
        stats=stats,
        recent_books=[BookResponse.model_validate(book) for book in recent_books],
        popular_books=[BookResponse.model_validate(book) for book in popular_books]
    )

@router.post("/books", response_model=BookResponse)
async def create_book(
    title: str = Form(...),
    author: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    is_free: bool = Form(True),
    cover_file: UploadFile = File(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Создание новой книги"""
    
    # Проверка категории
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Сохранение обложки
    cover_url = await save_and_optimize_image(cover_file)
    
    # Сохранение аудиофайла
    audio_url, duration_seconds = await save_audio_file(audio_file)
    
    # Создание записи в БД
    book = Book(
        title=title,
        author=author,
        description=description,
        category_id=category_id,
        is_free=is_free,
        duration_seconds=duration_seconds,
        cover_url=cover_url,
        audio_file_url=audio_url,
        added_by_admin_id=admin.id
    )
    
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # Обновляем счетчик книг в категории
    category.books_count = db.query(Book).filter(
        Book.category_id == category_id,
        Book.is_active == True
    ).count()
    db.commit()
    
    return BookResponse.model_validate(book)

@router.get("/books", response_model=List[BookResponse])
async def get_admin_books(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Получение списка книг для админ панели"""
    
    query = db.query(Book)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Book.title.ilike(search_term) | 
            Book.author.ilike(search_term)
        )
    
    offset = (page - 1) * limit
    books = query.offset(offset).limit(limit).all()
    
    return [BookResponse.model_validate(book) for book in books]

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Обновление книги"""
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Обновление полей
    if book_data.title is not None:
        book.title = book_data.title
    if book_data.author is not None:
        book.author = book_data.author
    if book_data.description is not None:
        book.description = book_data.description
    if book_data.category_id is not None:
        book.category_id = book_data.category_id
    if book_data.is_free is not None:
        book.is_free = book_data.is_free
    if book_data.is_active is not None:
        book.is_active = book_data.is_active
    
    book.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(book)
    
    return BookResponse.model_validate(book)

@router.delete("/books/{book_id}", response_model=StatusResponse)
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Удаление книги"""
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Удаление файлов
    if book.cover_url:
        delete_file(book.cover_url.replace("/static", settings.upload_dir))
    if book.audio_file_url:
        delete_file(book.audio_file_url.replace("/static", settings.upload_dir))
    
    # Удаление из БД
    db.delete(book)
    db.commit()
    
    return StatusResponse(status="deleted", message=f"Book {book_id} deleted")

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Создание новой категории"""
    
    # Проверка уникальности
    existing = db.query(Category).filter(Category.name == category_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return CategoryResponse.model_validate(category)

@router.get("/categories", response_model=List[CategoryResponse])
async def get_admin_categories(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Получение всех категорий"""
    categories = db.query(Category).all()
    return [CategoryResponse.model_validate(category) for category in categories]

@router.get("/users", response_model=List[UserResponse])
async def get_admin_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Получение списка пользователей"""
    
    offset = (page - 1) * limit
    users = db.query(User).offset(offset).limit(limit).all()
    
    return [UserResponse.model_validate(user) for user in users]

@router.post("/setup-demo-data", response_model=StatusResponse)
async def setup_demo_data(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Создание демонстрационных данных"""
    
    try:
        # Создаем категории если их нет
        categories_data = [
            {"name": "Классика", "emoji": "📚"},
            {"name": "Фантастика", "emoji": "🚀"},
            {"name": "Детективы", "emoji": "🕵️"},
            {"name": "Романы", "emoji": "❤️"},
            {"name": "Бизнес", "emoji": "💼"},
            {"name": "Психология", "emoji": "🧠"},
            {"name": "История", "emoji": "🏛️"},
            {"name": "Биографии", "emoji": "👤"}
        ]
        
        for cat_data in categories_data:
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                category = Category(**cat_data)
                db.add(category)
        
        db.commit()
        
        return StatusResponse(
            status="success", 
            message="Демонстрационные данные созданы успешно"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books", response_model=List[BookResponse])
async def get_admin_books(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Получение списка книг для админа"""
    
    offset = (page - 1) * limit
    books = db.query(Book).offset(offset).limit(limit).all()
    
    return [BookResponse.model_validate(book) for book in books] 