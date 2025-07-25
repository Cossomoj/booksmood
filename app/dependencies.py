from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .auth import get_current_user, get_current_admin, get_optional_user
from .models import User, Admin

# Re-export dependencies for convenience
get_db = get_db
get_current_user = get_current_user
get_current_admin = get_current_admin
get_optional_user = get_optional_user

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