from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional

from ..database import get_db
from ..schemas import BookResponse, BooksListResponse, SearchResponse, UserProgress
from ..models import Book, Category, ListeningHistory, Favorite, User
from ..dependencies import get_current_user, get_optional_user

router = APIRouter(prefix="/api/books", tags=["books"])

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
    limit: int = Query(20, le=100, description="Количество книг"),
    offset: int = Query(0, ge=0, description="Смещение"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Получение списка книг"""
    
    query = db.query(Book).filter(Book.is_active == True)
    
    if category_id:
        query = query.filter(Book.category_id == category_id)
    
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