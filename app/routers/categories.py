from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import CategoryResponse
from ..models import Category
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получение списка всех категорий"""
    categories = db.query(Category).all()
    return [CategoryResponse.model_validate(category) for category in categories] 