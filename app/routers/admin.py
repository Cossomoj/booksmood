from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case, text
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional

from ..database import get_db
from ..schemas import (
    AdminLogin, AdminToken, AdminResponse, DashboardResponse, DashboardStats,
    BookCreate, BookUpdate, BookResponse, CategoryCreate, CategoryResponse,
    StatusResponse, UserResponse, AdvancedDashboardResponse, AdvancedDashboardStats,
    UserActivityStats, ListeningTrends, TimeSeriesPoint, BookAnalytics,
    CategoryAnalytics, TopContent
)
from ..models import Admin, User, Book, Category, ListeningHistory, Favorite, Rating, Bookmark
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

@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Обновление информации о книге"""
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Обновляем только переданные поля
    for field, value in book_update.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    
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
    
    # Удаляем файлы если они есть
    if book.audio_file_url:
        try:
            import os
            from ..config import settings
            audio_path = book.audio_file_url.replace("/static/uploads/", "")
            full_path = os.path.join(settings.upload_dir, audio_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Warning: Could not delete audio file: {e}")
    
    if book.cover_url:
        try:
            import os
            from ..config import settings
            cover_path = book.cover_url.replace("/static/uploads/", "")
            full_path = os.path.join(settings.upload_dir, cover_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Warning: Could not delete cover file: {e}")
    
    # Удаляем связанные записи
    db.query(ListeningHistory).filter(ListeningHistory.book_id == book_id).delete()
    db.query(Favorite).filter(Favorite.book_id == book_id).delete()
    
    # Удаляем книгу
    db.delete(book)
    db.commit()
    
    return StatusResponse(status="success", message="Book deleted successfully")

@router.post("/books/{book_id}/toggle-status", response_model=BookResponse)
async def toggle_book_status(
    book_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Переключение статуса активности книги"""
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book.is_active = not book.is_active
    db.commit()
    db.refresh(book)
    
    return BookResponse.model_validate(book) 

# Добавляем импорты для расширенной аналитики
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, case, text

# Добавляем новые импорты схем
from ..schemas import (
    AdminLogin, AdminToken, AdminResponse, DashboardResponse, DashboardStats,
    BookCreate, BookUpdate, BookResponse, CategoryCreate, CategoryResponse,
    StatusResponse, UserResponse, AdvancedDashboardResponse, AdvancedDashboardStats,
    UserActivityStats, ListeningTrends, TimeSeriesPoint, BookAnalytics,
    CategoryAnalytics, TopContent
)
from ..models import Admin, User, Book, Category, ListeningHistory, Favorite, Rating, Bookmark

@router.get("/analytics", response_model=AdvancedDashboardResponse)
async def get_advanced_analytics(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Получение расширенной аналитики для админ панели"""
    
    now = datetime.utcnow()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # === БАЗОВАЯ СТАТИСТИКА ===
    total_users = db.query(User).count()
    total_books = db.query(Book).filter(Book.is_active == True).count()
    total_plays = db.query(func.sum(ListeningHistory.play_count)).scalar() or 0
    new_users_today = db.query(User).filter(func.date(User.created_at) == today).count()
    
    # === АКТИВНОСТЬ ПОЛЬЗОВАТЕЛЕЙ ===
    active_users_today = db.query(User.id).join(ListeningHistory).filter(
        func.date(ListeningHistory.updated_at) == today
    ).distinct().count()
    
    active_users_week = db.query(User.id).join(ListeningHistory).filter(
        ListeningHistory.updated_at >= week_ago
    ).distinct().count()
    
    active_users_month = db.query(User.id).join(ListeningHistory).filter(
        ListeningHistory.updated_at >= month_ago
    ).distinct().count()
    
    new_users_week = db.query(User).filter(User.created_at >= week_ago).count()
    new_users_month = db.query(User).filter(User.created_at >= month_ago).count()
    
    # Средняя продолжительность сессии
    avg_session_duration = db.query(func.avg(
        ListeningHistory.last_position / 60.0
    )).scalar() or 0.0
    
    user_activity = UserActivityStats(
        total_users=total_users,
        active_users_today=active_users_today,
        active_users_week=active_users_week,
        active_users_month=active_users_month,
        new_users_today=new_users_today,
        new_users_week=new_users_week,
        new_users_month=new_users_month,
        average_session_duration=avg_session_duration
    )
    
    # === ТРЕНДЫ ПРОСЛУШИВАНИЯ ===
    total_listening_time = db.query(func.sum(
        ListeningHistory.last_position / 3600.0
    )).scalar() or 0.0
    
    total_sessions = db.query(ListeningHistory).count()
    
    # Самый популярный час (упрощенно)
    peak_hour = 14  # Можно улучшить с реальными данными
    
    # Самый популярный день недели
    most_popular_day = "Понедельник"  # Можно улучшить с реальными данными
    
    # Коэффициент завершения
    completion_rate = db.query(func.avg(
        case(
            (Book.duration_seconds > 0, 
             ListeningHistory.last_position / Book.duration_seconds),
            else_=0
        ) * 100
    )).join(Book).scalar() or 0.0
    
    listening_trends = ListeningTrends(
        total_hours_listened=total_listening_time,
        total_sessions=total_sessions,
        average_session_duration=avg_session_duration,
        peak_listening_hour=peak_hour,
        most_popular_day=most_popular_day,
        completion_rate=completion_rate
    )
    
    # === ВРЕМЕННЫЕ РЯДЫ (последние 30 дней) ===
    daily_stats = []
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        new_users = db.query(User).filter(func.date(User.created_at) == date).count()
        
        # Часы прослушивания за день
        listening_hours = db.query(func.sum(
            ListeningHistory.last_position / 3600.0
        )).filter(func.date(ListeningHistory.updated_at) == date).scalar() or 0
        
        # Активные пользователи за день
        active_users = db.query(User.id).join(ListeningHistory).filter(
            func.date(ListeningHistory.updated_at) == date
        ).distinct().count()
        
        daily_stats.append({
            'date': date_str,
            'new_users': new_users,
            'listening_hours': int(listening_hours),
            'active_users': active_users
        })
    
    # Разворачиваем для правильного порядка (от старых к новым)
    daily_stats.reverse()
    
    daily_new_users = [TimeSeriesPoint(date=d['date'], value=d['new_users']) for d in daily_stats]
    daily_listening_hours = [TimeSeriesPoint(date=d['date'], value=d['listening_hours']) for d in daily_stats]
    daily_active_users = [TimeSeriesPoint(date=d['date'], value=d['active_users']) for d in daily_stats]
    
    # === ТОП КОНТЕНТ ===
    
    # Топ книги по популярности
    top_books_query = db.query(
        Book.id,
        Book.title,
        Book.author,
        Book.plays_count,
        func.count(Favorite.id).label('favorites_count'),
        func.coalesce(func.avg(Rating.rating), 0).label('avg_rating'),
        func.count(Rating.id).label('total_ratings'),
        (func.avg(ListeningHistory.last_position) / Book.duration_seconds * 100).label('completion_rate'),
        func.count(
            case((ListeningHistory.updated_at >= week_ago, 1))
        ).label('recent_activity')
    ).outerjoin(Favorite).outerjoin(Rating).outerjoin(ListeningHistory).filter(
        Book.is_active == True
    ).group_by(Book.id).order_by(desc(Book.plays_count)).limit(10)
    
    top_books_data = top_books_query.all()
    top_books = [
        BookAnalytics(
            id=book.id,
            title=book.title,
            author=book.author,
            plays_count=book.plays_count,
            favorites_count=book.favorites_count or 0,
            average_rating=float(book.avg_rating or 0),
            total_ratings=book.total_ratings or 0,
            completion_rate=float(book.completion_rate or 0),
            recent_activity=book.recent_activity or 0
        ) for book in top_books_data
    ]
    
    # Топ категории
    top_categories_query = db.query(
        Category.id,
        Category.name,
        Category.emoji,
        func.count(Book.id).label('books_count'),
        func.sum(Book.plays_count).label('total_plays'),
        func.count(func.distinct(ListeningHistory.user_id)).label('unique_listeners'),
        func.coalesce(func.avg(Rating.rating), 0).label('avg_rating')
    ).outerjoin(Book).outerjoin(ListeningHistory, Book.id == ListeningHistory.book_id).outerjoin(
        Rating, Book.id == Rating.book_id
    ).filter(Book.is_active == True).group_by(Category.id).order_by(
        desc('total_plays')
    ).limit(10)
    
    top_categories_data = top_categories_query.all()
    top_categories = [
        CategoryAnalytics(
            id=cat.id,
            name=cat.name,
            emoji=cat.emoji,
            books_count=cat.books_count or 0,
            total_plays=cat.total_plays or 0,
            unique_listeners=cat.unique_listeners or 0,
            average_book_rating=float(cat.avg_rating or 0)
        ) for cat in top_categories_data
    ]
    
    # Трендовые книги (по росту популярности за неделю)
    trending_books = top_books[:5]  # Упрощенно - можно улучшить
    
    top_content = TopContent(
        top_books=top_books,
        top_categories=top_categories,
        trending_books=trending_books
    )
    
    # === ПОСЛЕДНИЕ КНИГИ ===
    recent_books = db.query(Book).filter(
        Book.is_active == True
    ).order_by(desc(Book.created_at)).limit(5).all()
    
    # === ФИНАЛЬНАЯ СТАТИСТИКА ===
    advanced_stats = AdvancedDashboardStats(
        total_users=total_users,
        total_books=total_books,
        total_plays=total_plays,
        new_users_today=new_users_today,
        user_activity=user_activity,
        listening_trends=listening_trends,
        daily_new_users=daily_new_users,
        daily_listening_hours=daily_listening_hours,
        daily_active_users=daily_active_users
    )
    
    return AdvancedDashboardResponse(
        stats=advanced_stats,
        top_content=top_content,
        recent_books=[BookResponse.model_validate(book) for book in recent_books]
    ) 