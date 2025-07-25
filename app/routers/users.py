from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime

from ..database import get_db
from ..schemas import (
    UserLibrary, HistoryUpdate, StatusResponse, FavoriteResponse,
    HistoryResponse, BookResponse, UserStats
)
from ..models import User, Book, ListeningHistory, Favorite
from ..dependencies import get_current_user
from ..utils import calculate_progress_percent

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/library", response_model=UserLibrary)
async def get_user_library(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение библиотеки пользователя"""
    
    # История прослушивания
    history_query = db.query(ListeningHistory).filter(
        ListeningHistory.user_id == current_user.id
    ).order_by(desc(ListeningHistory.last_played))
    
    history_items = []
    for history in history_query.all():
        book = history.book
        if book and book.is_active:
            progress_percent = calculate_progress_percent(
                history.current_position, 
                history.total_duration or book.duration_seconds or 0
            )
            
            history_items.append(HistoryResponse(
                book=BookResponse.model_validate(book),
                current_position=history.current_position,
                progress_percent=progress_percent,
                last_played=history.last_played,
                is_finished=history.is_finished
            ))
    
    # Избранные книги
    favorites_query = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(desc(Favorite.added_at))
    
    favorite_books = []
    for favorite in favorites_query.all():
        book = favorite.book
        if book and book.is_active:
            favorite_books.append(BookResponse.model_validate(book))
    
    # Статистика
    total_books = history_query.count()
    finished_books = history_query.filter(ListeningHistory.is_finished == True).count()
    
    # Общее время прослушивания (приблизительно)
    total_time_result = db.query(
        func.sum(ListeningHistory.current_position)
    ).filter(ListeningHistory.user_id == current_user.id).scalar()
    
    total_time_seconds = total_time_result or 0
    favorite_count = len(favorite_books)
    
    stats = UserStats(
        total_books=total_books,
        finished_books=finished_books,
        total_time_seconds=total_time_seconds,
        favorite_count=favorite_count
    )
    
    return UserLibrary(
        history=history_items,
        favorites=favorite_books,
        stats=stats
    )

@router.post("/history/{book_id}", response_model=StatusResponse)
async def update_listening_progress(
    book_id: int,
    progress: HistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление прогресса прослушивания"""
    
    # Проверка существования книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Поиск или создание записи истории
    history = db.query(ListeningHistory).filter(
        ListeningHistory.user_id == current_user.id,
        ListeningHistory.book_id == book_id
    ).first()
    
    if not history:
        history = ListeningHistory(
            user_id=current_user.id,
            book_id=book_id,
            current_position=progress.position,
            total_duration=progress.duration,
            last_played=datetime.utcnow()
        )
        db.add(history)
    else:
        history.current_position = progress.position
        history.total_duration = progress.duration
        history.last_played = datetime.utcnow()
        history.play_count += 1
    
    # Определение завершенности
    if progress.duration > 0:
        progress_percent = (progress.position / progress.duration) * 100
        history.is_finished = progress_percent >= 95  # 95% считается завершенным
    
    # Обновление счетчика прослушиваний книги
    book.plays_count = db.query(ListeningHistory).filter(
        ListeningHistory.book_id == book_id
    ).count()
    
    db.commit()
    
    progress_percent = calculate_progress_percent(progress.position, progress.duration)
    
    return StatusResponse(
        status="success",
        message=f"Progress updated: {progress_percent}%"
    )

@router.post("/favorites/{book_id}", response_model=FavoriteResponse)
async def add_to_favorites(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Добавление книги в избранное"""
    
    # Проверка существования книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Проверка, не в избранном ли уже
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()
    
    if existing:
        return FavoriteResponse(status="already_added", book_id=book_id)
    
    # Добавление в избранное
    favorite = Favorite(
        user_id=current_user.id,
        book_id=book_id
    )
    db.add(favorite)
    db.commit()
    
    return FavoriteResponse(status="added", book_id=book_id)

@router.delete("/favorites/{book_id}", response_model=FavoriteResponse)
async def remove_from_favorites(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление книги из избранного"""
    
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Book not in favorites")
    
    db.delete(favorite)
    db.commit()
    
    return FavoriteResponse(status="removed", book_id=book_id) 