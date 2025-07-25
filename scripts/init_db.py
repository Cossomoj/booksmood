#!/usr/bin/env python3
"""
Скрипт инициализации базы данных AudioFlow
"""
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine, SessionLocal
from app.models import Base, Category, Admin
from app.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tables():
    """Создание всех таблиц в базе данных"""
    print("Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно")

def create_default_categories():
    """Создание стандартных категорий"""
    print("Создание категорий по умолчанию...")
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже категории
        existing_count = db.query(Category).count()
        if existing_count > 0:
            print(f"⚠️  Категории уже существуют ({existing_count} шт.), пропускаем создание")
            return
        
        default_categories = [
            {"name": "Классика", "emoji": "📚"},
            {"name": "Фантастика", "emoji": "🚀"},
            {"name": "Детективы", "emoji": "🕵️"},
            {"name": "Романы", "emoji": "❤️"},
            {"name": "Бизнес", "emoji": "💼"},
            {"name": "Психология", "emoji": "🧠"},
            {"name": "Саморазвитие", "emoji": "📈"},
            {"name": "История", "emoji": "🏛️"},
            {"name": "Биографии", "emoji": "👤"},
            {"name": "Ужасы", "emoji": "👻"},
            {"name": "Приключения", "emoji": "🗺️"},
            {"name": "Научпоп", "emoji": "🔬"},
        ]
        
        for cat_data in default_categories:
            category = Category(**cat_data)
            db.add(category)
        
        db.commit()
        print(f"✅ Создано {len(default_categories)} категорий")
        
    except Exception as e:
        print(f"❌ Ошибка при создании категорий: {e}")
        db.rollback()
    finally:
        db.close()

def create_admin_user():
    """Создание администратора по умолчанию"""
    print("Создание администратора по умолчанию...")
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже администраторы
        existing_admin = db.query(Admin).first()
        if existing_admin:
            print("⚠️  Администратор уже существует, пропускаем создание")
            return
        
        admin = Admin(
            username="admin",
            email="admin@audioflow.com",
            password_hash=pwd_context.hash("admin123"),
            is_superadmin=True
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Создан администратор:")
        print("   Логин: admin")
        print("   Пароль: admin123")
        print("   ⚠️  ОБЯЗАТЕЛЬНО смените пароль в продакшене!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании администратора: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Основная функция инициализации"""
    print("🎧 Инициализация базы данных AudioFlow")
    print("=" * 50)
    
    try:
        # Создание таблиц
        create_tables()
        
        # Создание категорий по умолчанию
        create_default_categories()
        
        # Создание администратора
        create_admin_user()
        
        print("\n" + "=" * 50)
        print("🎉 Инициализация завершена успешно!")
        print("\nСледующие шаги:")
        print("1. Запустите сервер: uvicorn app.main:app --reload")
        print("2. Откройте админ панель: http://localhost:8000/admin/login")
        print("3. Войдите как admin/admin123")
        print("4. Добавьте книги через админ панель")
        
    except Exception as e:
        print(f"\n❌ Ошибка инициализации: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 