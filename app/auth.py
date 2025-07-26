import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from typing import Optional, Dict

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, Admin

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

def validate_telegram_data(init_data: str, bot_token: str) -> Optional[Dict]:
    """Валидация данных от Telegram Web App"""
    try:
        if not init_data or not bot_token:
            print("Missing init_data or bot_token")
            return None
            
        parsed_data = parse_qs(init_data)
        
        # Извлекаем hash
        hash_value = parsed_data.get('hash', [''])[0]
        if not hash_value:
            print("No hash found in init_data")
            return None
        
        # Создаем data-check-string
        data_pairs = []
        for key, values in parsed_data.items():
            if key != 'hash' and values:
                data_pairs.append(f"{key}={values[0]}")
        
        data_check_string = '\n'.join(sorted(data_pairs))
        
        # Проверяем подпись
        secret_key = hmac.new(
            b"WebAppData", 
            bot_token.encode(), 
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != hash_value:
            print(f"Hash mismatch: calculated={calculated_hash}, received={hash_value}")
            return None
            
        # Проверяем время (расширяем до 7 дней для удобства разработки)
        auth_date = int(parsed_data.get('auth_date', ['0'])[0])
        current_time = time.time()
        time_diff = current_time - auth_date
        
        if time_diff > 604800:  # 7 дней вместо 24 часов
            print(f"Data too old: {time_diff} seconds ago")
            return None
            
        # Парсим user data
        user_data_str = parsed_data.get('user', ['{}'])[0]
        user_data = json.loads(user_data_str)
        
        # Дополнительные проверки user данных
        if not user_data.get('id'):
            print("No user ID in data")
            return None
            
        print(f"Telegram auth successful for user {user_data.get('id')}")
        return user_data
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"Error validating telegram data: {e}")
        return None

def create_test_user_data() -> Dict:
    """Создание тестовых данных пользователя для разработки"""
    return {
        "id": 12345678,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "ru"
    }

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_admin_token(admin_id: int) -> str:
    """Создание JWT токена для админа"""
    expire = datetime.utcnow() + timedelta(days=1)
    to_encode = {
        "sub": str(admin_id),
        "type": "admin",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """Получение текущего администратора из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "admin":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        admin_id = int(payload.get("sub"))
        admin = db.query(Admin).filter(Admin.id == admin_id, Admin.is_active == True).first()
        
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
            
        return admin
    except JWTError:
        raise credentials_exception

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получение пользователя из токена (опционально)"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except JWTError:
        return None 