from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..schemas import TelegramAuth, Token, UserResponse
from ..auth import validate_telegram_data, create_access_token, create_test_user_data
from ..models import User
from ..config import settings
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/telegram", response_model=Token)
async def telegram_auth(auth_data: TelegramAuth, db: Session = Depends(get_db)):
    """Авторизация через Telegram Web App"""
    
    # Валидация данных от Telegram
    user_data = validate_telegram_data(auth_data.initData, settings.bot_token)
    
    if not user_data:
        # В режиме разработки возвращаем детальную ошибку
        if settings.debug:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Invalid authentication data",
                    "debug_info": "Check bot token and initData format",
                    "received_data_length": len(auth_data.initData) if auth_data.initData else 0
                }
            )
        else:
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
        print(f"Created new user: {user.telegram_id}")
    else:
        # Обновление данных существующего пользователя
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")
        db.commit()
        print(f"Updated existing user: {user.telegram_id}")
    
    # Создание JWT токена
    access_token = create_access_token(
        data={"sub": str(user.id)},
    )
    
    user_response = UserResponse.model_validate(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/test", response_model=Token)
async def test_auth(
    db: Session = Depends(get_db),
    dev_mode: bool = Query(True, description="Development mode")
):
    """Тестовая авторизация для разработки (только в debug режиме)"""
    
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
        )
    
    # Создаем тестовые данные пользователя
    test_data = create_test_user_data()
    telegram_id = test_data.get("id")
    
    # Поиск или создание тестового пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=test_data.get("username"),
            first_name=test_data.get("first_name"),
            last_name=test_data.get("last_name")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user: {user.telegram_id}")
    
    # Создание JWT токена
    access_token = create_access_token(
        data={"sub": str(user.id)},
    )
    
    user_response = UserResponse.model_validate(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение информации о текущем пользователе"""
    return UserResponse.model_validate(current_user) 