from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TelegramAuth, Token, UserResponse
from ..auth import validate_telegram_data, create_access_token
from ..models import User
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/telegram", response_model=Token)
async def telegram_auth(auth_data: TelegramAuth, db: Session = Depends(get_db)):
    """Авторизация через Telegram Web App"""
    
    # Валидация данных от Telegram
    user_data = validate_telegram_data(auth_data.initData, settings.bot_token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data"
        )
    
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data"
        )
    
    # Поиск или создание пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        # Создание нового пользователя
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Обновление данных существующего пользователя
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")
        db.commit()
    
    # Создание JWT токена
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    } 