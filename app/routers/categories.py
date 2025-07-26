from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import CategoryResponse
from ..models import Category


router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db)
):
    """Получение списка всех категорий"""
    categories = db.query(Category).all()
    return [CategoryResponse.model_validate(category) for category in categories] 