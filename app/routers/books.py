from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from typing import List, Optional
from enum import Enum
import re

from fastapi.responses import StreamingResponse
import os
from ..config import settings

from ..database import get_db
from ..schemas import BookResponse, BooksListResponse, SearchResponse, UserProgress
from ..models import Book, Category, ListeningHistory, Favorite, User
from ..dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/api/books", tags=["books"])

class SortBy(str, Enum):
    newest = "newest"
    oldest = "oldest"
    popular = "popular"
    rating = "rating"
    alphabetical = "alphabetical"
    duration_short = "duration_short"
    duration_long = "duration_long"

def get_user_progress(book: Book, user: Optional[User], db: Session) -> Optional[UserProgress]:
    """Получение прогресса пользователя для книги"""
    if not user:
        return None
    
    # История прослушивания
    history = db.query(ListeningHistory).filter(
        ListeningHistory.user_id == user.id,
        ListeningHistory.book_id == book.id
    ).first()
    
    # Избранное
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.book_id == book.id
    ).first()
    
    return UserProgress(
        current_position=history.current_position if history else 0,
        is_finished=history.is_finished if history else False,
        is_favorite=bool(favorite),
        last_played=history.last_played if history else None
    )

@router.get("", response_model=BooksListResponse)
async def get_books(
    category_id: Optional[int] = Query(None, description="ID категории"),
    is_free: Optional[bool] = Query(None, description="Только бесплатные книги"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Минимальный рейтинг"),
    min_duration: Optional[int] = Query(None, ge=0, description="Минимальная длительность в секундах"),
    max_duration: Optional[int] = Query(None, ge=0, description="Максимальная длительность в секундах"),
    author: Optional[str] = Query(None, description="Поиск по автору"),
    sort_by: SortBy = Query(SortBy.newest, description="Сортировка"),
    limit: int = Query(20, le=100, description="Количество книг"),
    offset: int = Query(0, ge=0, description="Смещение"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Получение списка книг с расширенными фильтрами"""
    
    query = db.query(Book).filter(Book.is_active == True)
    
    # Применяем фильтры
    if category_id:
        query = query.filter(Book.category_id == category_id)
    
    if is_free is not None:
        query = query.filter(Book.is_free == is_free)
    
    if min_rating is not None:
        query = query.filter(Book.rating >= min_rating)
    
    if min_duration is not None:
        query = query.filter(Book.duration_seconds >= min_duration)
    
    if max_duration is not None:
        query = query.filter(Book.duration_seconds <= max_duration)
    
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    
    # Применяем сортировку
    if sort_by == SortBy.newest:
        query = query.order_by(desc(Book.created_at))
    elif sort_by == SortBy.oldest:
        query = query.order_by(asc(Book.created_at))
    elif sort_by == SortBy.popular:
        query = query.order_by(desc(Book.plays_count))
    elif sort_by == SortBy.rating:
        query = query.order_by(desc(Book.rating))
    elif sort_by == SortBy.alphabetical:
        query = query.order_by(asc(Book.title))
    elif sort_by == SortBy.duration_short:
        query = query.order_by(asc(Book.duration_seconds))
    elif sort_by == SortBy.duration_long:
        query = query.order_by(desc(Book.duration_seconds))
    
    total = query.count()
    books = query.offset(offset).limit(limit).all()
    
    # Обогащение данных о прогрессе пользователя
    books_response = []
    for book in books:
        book_dict = BookResponse.model_validate(book).model_dump()
        book_dict["user_progress"] = get_user_progress(book, current_user, db)
        books_response.append(BookResponse(**book_dict))
    
    return BooksListResponse(
        books=books_response,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/search", response_model=SearchResponse)
async def search_books(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(20, le=100, description="Количество результатов"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Поиск книг по названию и автору"""
    
    search_term = f"%{q}%"
    
    books = db.query(Book).filter(
        Book.is_active == True,
        or_(
            Book.title.ilike(search_term),
            Book.author.ilike(search_term),
            Book.description.ilike(search_term)
        )
    ).limit(limit).all()
    
    # Обогащение данных о прогрессе пользователя
    books_response = []
    for book in books:
        book_dict = BookResponse.model_validate(book).model_dump()
        book_dict["user_progress"] = get_user_progress(book, current_user, db)
        books_response.append(BookResponse(**book_dict))
    
    return SearchResponse(
        books=books_response,
        query=q,
        total=len(books_response)
    )

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Получение детальной информации о книге"""
    
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Обогащение данных о прогрессе пользователя
    book_dict = BookResponse.model_validate(book).model_dump()
    book_dict["user_progress"] = get_user_progress(book, current_user, db)
    
    return BookResponse(**book_dict) 

@router.get("/{book_id}/audio")
async def stream_audio(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Потоковая передача аудиофайла книги с поддержкой Range requests"""
    
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book or not book.audio_file_url:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Получаем путь к файлу
    audio_path = book.audio_file_url.replace("/static/uploads/", "")
    file_path = os.path.join(settings.upload_dir, audio_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    # Получаем размер файла
    file_size = os.path.getsize(file_path)
    
    # Обрабатываем Range заголовок для потокового воспроизведения
    range_header = request.headers.get("range")
    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            def iterfile(file_path: str, start: int, end: int, chunk_size: int = 8192):
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = f.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            content_length = end - start + 1
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": "audio/mpeg"
            }
            
            return StreamingResponse(
                iterfile(file_path, start, end),
                status_code=206,
                headers=headers
            )
    
    # Обычная передача файла
    def iterfile(file_path: str, chunk_size: int = 8192):
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk
    
    headers = {
        "Content-Length": str(file_size),
        "Content-Type": "audio/mpeg",
        "Accept-Ranges": "bytes"
    }
    
    return StreamingResponse(iterfile(file_path), headers=headers) 