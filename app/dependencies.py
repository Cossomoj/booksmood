from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union
from jose import JWTError, jwt

from .database import get_db
from .auth import get_current_user, get_current_admin, get_optional_user
from .models import User, Admin
from .config import settings

# Re-export dependencies for convenience
get_db = get_db
get_current_user = get_current_user
get_current_admin = get_current_admin
get_optional_user = get_optional_user

security = HTTPBearer()

async def get_user_or_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Union[User, Admin, None]:
    """Получение пользователя или админа из токена"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        
        # Проверяем тип токена
        token_type = payload.get("type")
        user_id = int(payload.get("sub"))
        
        if token_type == "admin":
            # Админский токен
            admin = db.query(Admin).filter(Admin.id == user_id, Admin.is_active == True).first()
            return admin
        else:
            # Пользовательский токен
            user = db.query(User).filter(User.id == user_id).first()
            return user
            
    except (JWTError, ValueError):
        return None

def get_superadmin(admin: Admin = Depends(get_current_admin)) -> Admin:
    """Проверка, что текущий админ является суперадмином"""
    if not admin.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return admin

def get_premium_user(user: User = Depends(get_current_user)) -> User:
    """Проверка, что пользователь имеет premium статус"""
    if not user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return user 