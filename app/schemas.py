from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Telegram Auth Schemas
class TelegramAuth(BaseModel):
    initData: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: 'UserResponse'

# User Schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_premium: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    emoji: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    books_count: int
    
    class Config:
        from_attributes = True

# Book Schemas
class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_free: bool = True

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_free: Optional[bool] = None
    is_active: Optional[bool] = None

class UserProgress(BaseModel):
    current_position: int
    is_finished: bool
    is_favorite: bool
    last_played: Optional[datetime] = None

class BookResponse(BookBase):
    id: int
    duration_seconds: Optional[int] = None
    cover_url: Optional[str] = None
    audio_file_url: Optional[str] = None
    rating: float
    plays_count: int
    is_active: bool
    created_at: datetime
    category: Optional[CategoryResponse] = None
    user_progress: Optional[UserProgress] = None
    
    class Config:
        from_attributes = True

class BooksListResponse(BaseModel):
    books: List[BookResponse]
    total: int
    limit: int
    offset: int

# History Schemas
class HistoryUpdate(BaseModel):
    position: int
    duration: int

class HistoryResponse(BaseModel):
    book: BookResponse
    current_position: int
    progress_percent: float
    last_played: datetime
    is_finished: bool
    
    class Config:
        from_attributes = True

# Admin Schemas
class AdminLogin(BaseModel):
    username: str
    password: str

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str
    is_superadmin: bool = False

class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superadmin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AdminToken(BaseModel):
    access_token: str
    token_type: str
    admin: AdminResponse

# Library Schemas
class UserStats(BaseModel):
    total_books: int
    finished_books: int
    total_time_seconds: int
    favorite_count: int

class UserLibrary(BaseModel):
    history: List[HistoryResponse]
    favorites: List[BookResponse]
    stats: UserStats

# Search Schemas
class SearchResponse(BaseModel):
    books: List[BookResponse]
    query: str
    total: int

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_users: int
    total_books: int
    total_plays: int
    new_users_today: int

class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_books: List[BookResponse]
    popular_books: List[BookResponse]

# Response Schemas
class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None

class FavoriteResponse(BaseModel):
    status: str
    book_id: int

# Rating Schemas
class RatingBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
    comment: Optional[str] = None

class RatingCreate(BaseModel):
    book_id: int
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")
    review: Optional[str] = Field(None, max_length=1000, description="Отзыв")

class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class RatingResponse(RatingBase):
    id: int
    user_id: int
    book_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BookRating(BaseModel):
    average_rating: float
    total_ratings: int
    user_rating: Optional[int] = None

# Bookmark Schemas
class BookmarkBase(BaseModel):
    position: int = Field(..., ge=0, description="Позиция в секундах")
    title: Optional[str] = Field(None, max_length=200, description="Название закладки")

class BookmarkCreate(BaseModel):
    book_id: int
    position: float  # Позиция в секундах
    title: Optional[str] = None
    note: Optional[str] = None

class BookmarkUpdate(BaseModel):
    position: Optional[int] = Field(None, ge=0)
    title: Optional[str] = Field(None, max_length=200)

class BookmarkResponse(BookmarkBase):
    id: int
    user_id: int
    book_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True 

# Advanced Admin Analytics Schemas
class TimeSeriesPoint(BaseModel):
    date: str
    value: int
    
class BookAnalytics(BaseModel):
    id: int
    title: str
    author: str
    plays_count: int
    favorites_count: int
    average_rating: float
    total_ratings: int
    completion_rate: float
    recent_activity: int  # прослушивания за последние 7 дней

class CategoryAnalytics(BaseModel):
    id: int
    name: str
    emoji: Optional[str] = None
    books_count: int
    total_plays: int
    unique_listeners: int
    average_book_rating: float

class UserActivityStats(BaseModel):
    total_users: int
    active_users_today: int
    active_users_week: int
    active_users_month: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    average_session_duration: float

class ListeningTrends(BaseModel):
    total_hours_listened: float
    total_sessions: int
    average_session_duration: float
    peak_listening_hour: int
    most_popular_day: str
    completion_rate: float

class AdvancedDashboardStats(BaseModel):
    # Базовая статистика
    total_users: int
    total_books: int
    total_plays: int
    new_users_today: int
    
    # Расширенная аналитика
    user_activity: UserActivityStats
    listening_trends: ListeningTrends
    
    # Временные ряды (последние 30 дней)
    daily_new_users: List[TimeSeriesPoint]
    daily_listening_hours: List[TimeSeriesPoint]
    daily_active_users: List[TimeSeriesPoint]

class TopContent(BaseModel):
    top_books: List[BookAnalytics]
    top_categories: List[CategoryAnalytics]
    trending_books: List[BookAnalytics]  # по росту популярности

class AdvancedDashboardResponse(BaseModel):
    stats: AdvancedDashboardStats
    top_content: TopContent
    recent_books: List[BookResponse] 