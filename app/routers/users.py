from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import List, Optional

from ..database import get_db
from ..schemas import (
    UserLibrary, HistoryUpdate, StatusResponse, FavoriteResponse,
    HistoryResponse, BookResponse, UserStats, RatingCreate, RatingUpdate,
    RatingResponse, BookRating, BookmarkCreate, BookmarkUpdate, BookmarkResponse
)
from ..models import User, Book, ListeningHistory, Favorite, Rating, Bookmark
from ..dependencies import get_current_user, get_optional_user
from ..utils import calculate_progress_percent

def get_user_progress(book: Book, user: User, db: Session):
    """Получение прогресса пользователя для книги"""
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
    
    return {
        "current_position": history.current_position if history else 0,
        "is_finished": history.is_finished if history else False,
        "is_favorite": bool(favorite),
        "last_played": history.last_played if history else None
    }

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

@router.post("/favorites/{book_id}", response_model=StatusResponse)
async def add_to_favorites(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Добавление книги в избранное"""
    
    # Проверяем что книга существует и активна
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Проверяем что книга еще не в избранном
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()
    
    if existing:
        return StatusResponse(
            status="already_exists",
            message="Книга уже в избранном"
        )
    
    # Добавляем в избранное
    favorite = Favorite(
        user_id=current_user.id,
        book_id=book_id
    )
    
    db.add(favorite)
    db.commit()
    
    print(f"User {current_user.id} added book {book_id} to favorites")
    
    return StatusResponse(
        status="success",
        message="Книга добавлена в избранное"
    )

@router.delete("/favorites/{book_id}", response_model=StatusResponse)
async def remove_from_favorites(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление книги из избранного"""
    
    # Ищем запись в избранном
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=404, 
            detail="Книга не найдена в избранном"
        )
    
    # Удаляем из избранного
    db.delete(favorite)
    db.commit()
    
    print(f"User {current_user.id} removed book {book_id} from favorites")
    
    return StatusResponse(
        status="success",
        message="Книга удалена из избранного"
    )

@router.get("/favorites", response_model=List[BookResponse])
async def get_user_favorites(
    limit: int = Query(50, le=100, description="Количество книг"),
    offset: int = Query(0, ge=0, description="Смещение"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка избранных книг пользователя"""
    
    # Получаем избранные книги с join
    favorites_query = db.query(Book).join(Favorite).filter(
        Favorite.user_id == current_user.id,
        Book.is_active == True
    ).order_by(desc(Favorite.added_at))
    
    favorites = favorites_query.offset(offset).limit(limit).all()
    
    # Обогащение данных о прогрессе пользователя
    favorites_response = []
    for book in favorites:
        book_dict = BookResponse.model_validate(book).model_dump()
        book_dict["user_progress"] = get_user_progress(book, current_user, db)
        favorites_response.append(BookResponse(**book_dict))
    
    return favorites_response

@router.get("/favorites/{book_id}/status")
async def check_favorite_status(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Проверка статуса книги в избранном"""
    
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()
    
    return {
        "book_id": book_id,
        "is_favorite": bool(favorite),
        "added_at": favorite.added_at if favorite else None
    }

@router.post("/history/{book_id}", response_model=StatusResponse)
async def update_listening_progress(
    book_id: int,
    progress: HistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление прогресса прослушивания"""
    
    # Проверяем существование книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Ищем существующую запись в истории
    history = db.query(ListeningHistory).filter(
        ListeningHistory.user_id == current_user.id,
        ListeningHistory.book_id == book_id
    ).first()
    
    if history:
        # Обновляем существующую запись
        history.current_position = progress.position
        history.total_duration = progress.duration
        history.last_played = datetime.utcnow()
        history.play_count += 1
        
        # Определяем, закончена ли книга (если прослушано более 95%)
        if progress.duration > 0:
            progress_percent = (progress.position / progress.duration) * 100
            history.is_finished = progress_percent >= 95.0
    else:
        # Создаем новую запись
        history = ListeningHistory(
            user_id=current_user.id,
            book_id=book_id,
            current_position=progress.position,
            total_duration=progress.duration,
            is_finished=False,
            play_count=1
        )
        db.add(history)
    
    # Обновляем счетчик воспроизведений книги
    book.plays_count += 1
    
    db.commit()
    
    return StatusResponse(
        status="success", 
        message=f"Progress updated: {progress.position}s / {progress.duration}s"
    )

@router.get("/history/{book_id}", response_model=dict)
async def get_listening_progress(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение прогресса прослушивания конкретной книги"""
    
    # Проверяем существование книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Ищем запись в истории
    history = db.query(ListeningHistory).filter(
        ListeningHistory.user_id == current_user.id,
        ListeningHistory.book_id == book_id
    ).first()
    
    if not history:
        return {
            "current_position": 0,
            "total_duration": book.duration_seconds,
            "progress_percent": 0.0,
            "is_finished": False,
            "play_count": 0,
            "last_played": None
        }
    
    progress_percent = calculate_progress_percent(
        history.current_position,
        history.total_duration or book.duration_seconds or 0
    )
    
    return {
        "current_position": history.current_position,
        "total_duration": history.total_duration or book.duration_seconds,
        "progress_percent": progress_percent,
        "is_finished": history.is_finished,
        "play_count": history.play_count,
        "last_played": history.last_played
    }

@router.post("/history/{book_id}/finish", response_model=StatusResponse)
async def mark_book_finished(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отметить книгу как прослушанную"""
    
    # Проверяем существование книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Ищем или создаем запись в истории
    history = db.query(ListeningHistory).filter(
        ListeningHistory.user_id == current_user.id,
        ListeningHistory.book_id == book_id
    ).first()
    
    if history:
        history.is_finished = True
        history.last_played = datetime.utcnow()
    else:
        history = ListeningHistory(
            user_id=current_user.id,
            book_id=book_id,
            current_position=book.duration_seconds or 0,
            total_duration=book.duration_seconds,
            is_finished=True,
            play_count=1
        )
        db.add(history)
    
    db.commit()
    
    return StatusResponse(status="success", message="Book marked as finished")

@router.post("/ratings/{book_id}", response_model=RatingResponse)
async def rate_book(
    book_id: int,
    rating_data: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Оценить книгу"""
    
    # Проверяем существование книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Ищем существующий рейтинг
    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.book_id == book_id
    ).first()
    
    if existing_rating:
        # Обновляем существующий рейтинг
        existing_rating.rating = rating_data.rating
        existing_rating.comment = rating_data.comment
        existing_rating.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_rating)
        
        # Обновляем средний рейтинг книги
        update_book_rating(book, db)
        
        return RatingResponse.model_validate(existing_rating)
    else:
        # Создаем новый рейтинг
        new_rating = Rating(
            user_id=current_user.id,
            book_id=book_id,
            rating=rating_data.rating,
            comment=rating_data.comment
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        
        # Обновляем средний рейтинг книги
        update_book_rating(book, db)
        
        return RatingResponse.model_validate(new_rating)

@router.get("/ratings/{book_id}", response_model=BookRating)
async def get_book_rating(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Получение рейтинга книги"""
    
    # Проверяем существование книги
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Вычисляем средний рейтинг
    rating_stats = db.query(
        func.avg(Rating.rating).label('average'),
        func.count(Rating.id).label('total')
    ).filter(Rating.book_id == book_id).first()
    
    average_rating = float(rating_stats.average) if rating_stats.average else 0.0
    total_ratings = rating_stats.total or 0
    
    # Получаем рейтинг текущего пользователя
    user_rating = None
    if current_user:
        user_rating_obj = db.query(Rating).filter(
            Rating.user_id == current_user.id,
            Rating.book_id == book_id
        ).first()
        user_rating = user_rating_obj.rating if user_rating_obj else None
    
    return BookRating(
        average_rating=round(average_rating, 1),
        total_ratings=total_ratings,
        user_rating=user_rating
    )

@router.delete("/ratings/{book_id}", response_model=StatusResponse)
async def delete_rating(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить свой рейтинг книги"""
    
    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.book_id == book_id
    ).first()
    
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    db.delete(rating)
    
    # Обновляем средний рейтинг книги
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        update_book_rating(book, db)
    
    db.commit()
    
    return StatusResponse(status="success", message="Rating deleted")

def update_book_rating(book: Book, db: Session):
    """Обновление среднего рейтинга книги"""
    rating_stats = db.query(
        func.avg(Rating.rating).label('average')
    ).filter(Rating.book_id == book.id).first()
    
    book.rating = float(rating_stats.average) if rating_stats.average else 0.0
    db.commit()

@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание новой закладки"""
    
    # Проверяем что книга существует и активна
    book = db.query(Book).filter(
        Book.id == bookmark_data.book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Проверяем валидность позиции
    if bookmark_data.position < 0:
        raise HTTPException(status_code=400, detail="Position cannot be negative")
    
    if book.duration_seconds and bookmark_data.position > book.duration_seconds:
        raise HTTPException(status_code=400, detail="Position exceeds book duration")
    
    # Создаем закладку
    bookmark = Bookmark(
        user_id=current_user.id,
        book_id=bookmark_data.book_id,
        position=bookmark_data.position,
        title=bookmark_data.title or f"Закладка {int(bookmark_data.position // 60)}:{int(bookmark_data.position % 60):02d}",
        note=bookmark_data.note
    )
    
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    
    print(f"User {current_user.id} created bookmark at {bookmark_data.position}s in book {bookmark_data.book_id}")
    
    return BookmarkResponse.model_validate(bookmark)

@router.get("/bookmarks/{book_id}", response_model=List[BookmarkResponse])
async def get_book_bookmarks(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение всех закладок пользователя для книги"""
    
    # Проверяем что книга существует
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Получаем закладки, отсортированные по позиции
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.book_id == book_id
    ).order_by(Bookmark.position).all()
    
    return [BookmarkResponse.model_validate(bookmark) for bookmark in bookmarks]

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def get_all_user_bookmarks(
    limit: int = Query(50, le=100, description="Количество закладок"),
    offset: int = Query(0, ge=0, description="Смещение"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение всех закладок пользователя"""
    
    bookmarks_query = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).order_by(desc(Bookmark.created_at))
    
    bookmarks = bookmarks_query.offset(offset).limit(limit).all()
    
    return [BookmarkResponse.model_validate(bookmark) for bookmark in bookmarks]

@router.put("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: int,
    bookmark_data: BookmarkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление закладки"""
    
    # Ищем закладку пользователя
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    # Обновляем поля
    if bookmark_data.title is not None:
        bookmark.title = bookmark_data.title
    if bookmark_data.note is not None:
        bookmark.note = bookmark_data.note
    if bookmark_data.position is not None:
        if bookmark_data.position < 0:
            raise HTTPException(status_code=400, detail="Position cannot be negative")
        bookmark.position = bookmark_data.position
    
    bookmark.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(bookmark)
    
    print(f"User {current_user.id} updated bookmark {bookmark_id}")
    
    return BookmarkResponse.model_validate(bookmark)

@router.delete("/bookmarks/{bookmark_id}", response_model=StatusResponse)
async def delete_bookmark(
    bookmark_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление закладки"""
    
    # Ищем закладку пользователя
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    
    print(f"User {current_user.id} deleted bookmark {bookmark_id}")
    
    return StatusResponse(
        status="success",
        message="Закладка удалена"
    ) 