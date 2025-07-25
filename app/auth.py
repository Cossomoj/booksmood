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

def validate_telegram_data(init_data: str, bot_token: str) -> Optional[Dict]:
    """Валидация данных от Telegram Web App"""
    try:
        parsed_data = parse_qs(init_data)
        
        # Извлекаем hash
        hash_value = parsed_data.get('hash', [''])[0]
        if not hash_value:
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
            return None
            
        # Проверяем время
        auth_date = int(parsed_data.get('auth_date', ['0'])[0])
        if time.time() - auth_date > 86400:  # 24 часа
            return None
            
        # Парсим user data
        user_data_str = parsed_data.get('user', ['{}'])[0]
        user_data = json.loads(user_data_str)
        return user_data
        
    except Exception as e:
        print(f"Error validating telegram data: {e}")
        return None

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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
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