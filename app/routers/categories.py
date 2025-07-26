from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Union, Optional

from ..database import get_db
from ..schemas import CategoryResponse
from ..models import Category, User, Admin
from ..dependencies import get_user_or_admin

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    user: Union[User, Admin, None] = Depends(get_user_or_admin)
):
    """Получение списка всех категорий (не требует авторизации)"""
    categories = db.query(Category).all()
    return [CategoryResponse.model_validate(category) for category in categories] 