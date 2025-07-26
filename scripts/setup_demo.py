#!/usr/bin/env python3
"""
Скрипт для создания демо-данных: категорий и тестовых книг
"""

import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Category, Book, Admin, Base
from app.utils import ensure_directory_exists
import requests
import urllib.request
from datetime import datetime

def create_demo_categories(db: Session):
    """Создание демо-категорий"""
    print("📚 Создаем демо-категории...")
    
    categories_data = [
        {"name": "Классика", "emoji": "📚"},
        {"name": "Фантастика", "emoji": "🚀"},
        {"name": "Детективы", "emoji": "🕵️"},
        {"name": "Романы", "emoji": "❤️"},
        {"name": "Бизнес", "emoji": "💼"},
        {"name": "Психология", "emoji": "🧠"},
        {"name": "История", "emoji": "🏛️"},
        {"name": "Биографии", "emoji": "👤"},
        {"name": "Саморазвитие", "emoji": "🌟"},
        {"name": "Философия", "emoji": "🤔"}
    ]
    
    created_count = 0
    for cat_data in categories_data:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
            created_count += 1
            print(f"  ✅ Создана категория: {cat_data['emoji']} {cat_data['name']}")
        else:
            print(f"  ⚠️  Категория уже существует: {cat_data['emoji']} {cat_data['name']}")
    
    db.commit()
    print(f"📊 Создано {created_count} новых категорий")
    return created_count

def download_demo_audio():
    """Загрузка демо аудиофайлов"""
    print("🎵 Загружаем демо аудиофайлы...")
    
    # Создаем директории
    audio_dir = Path("/app/app/static/uploads/audio")
    covers_dir = Path("/app/app/static/uploads/covers")
    ensure_directory_exists(str(audio_dir))
    ensure_directory_exists(str(covers_dir))
    
    # Демо аудиофайлы (короткие mp3 для тестирования)
    demo_files = {
        "demo1.mp3": {
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "title": "Классика - Колокола",
            "duration": 10
        },
        "demo2.mp3": {
            "url": "https://www.soundjay.com/misc/sounds/click-01.wav", 
            "title": "Детектив - Тайна",
            "duration": 15
        }
    }
    
    # Для демо создадим простые файлы
    demo_audio_content = b'\x00' * 1024  # Простой бинарный контент для демо
    
    demo_files_created = []
    for filename, info in demo_files.items():
        file_path = audio_dir / filename
        if not file_path.exists():
            with open(file_path, 'wb') as f:
                f.write(demo_audio_content)
            demo_files_created.append({
                "path": str(file_path),
                "url": f"/static/uploads/audio/{filename}",
                "title": info["title"],
                "duration": info["duration"]
            })
            print(f"  ✅ Создан демо-файл: {filename}")
    
    return demo_files_created

def create_demo_books(db: Session):
    """Создание демо-книг"""
    print("📖 Создаем демо-книги...")
    
    # Получаем категории
    categories = {cat.name: cat for cat in db.query(Category).all()}
    
    # Получаем первого админа или создаем
    admin = db.query(Admin).first()
    if not admin:
        print("⚠️  Админ не найден, создаем демо-админа...")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        admin = Admin(
            username="demo_admin",
            email="demo@booksmood.ru",
            password_hash=pwd_context.hash("demo123"),
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    
    # Демо-книги
    demo_books = [
        {
            "title": "Война и мир",
            "author": "Лев Толстой",
            "description": "Великий роман о жизни русского дворянства в эпоху войн с Наполеоном.",
            "category": "Классика",
            "duration_seconds": 144000,  # 40 часов
            "is_free": True
        },
        {
            "title": "Преступление и наказание", 
            "author": "Федор Достоевский",
            "description": "Психологический роман о студенте Раскольникове и его внутренней борьбе.",
            "category": "Классика",
            "duration_seconds": 72000,  # 20 часов
            "is_free": True
        },
        {
            "title": "Гарри Поттер и философский камень",
            "author": "Дж. К. Роулинг",
            "description": "Первая книга о юном волшебнике Гарри Поттере.",
            "category": "Фантастика", 
            "duration_seconds": 28800,  # 8 часов
            "is_free": False
        },
        {
            "title": "Шерлок Холмс: Этюд в багровых тонах",
            "author": "Артур Конан Дойль",
            "description": "Первое появление знаменитого детектива Шерлока Холмса.",
            "category": "Детективы",
            "duration_seconds": 18000,  # 5 часов
            "is_free": True
        },
        {
            "title": "Атомные привычки",
            "author": "Джеймс Клир",
            "description": "Как приобретать хорошие привычки и избавляться от плохих.",
            "category": "Саморазвитие",
            "duration_seconds": 36000,  # 10 часов
            "is_free": False
        },
        {
            "title": "Думай и богатей",
            "author": "Наполеон Хилл", 
            "description": "Классика литературы по саморазвитию и достижению успеха.",
            "category": "Бизнес",
            "duration_seconds": 32400,  # 9 часов
            "is_free": True
        },
        {
            "title": "Гордость и предубеждение",
            "author": "Джейн Остен",
            "description": "Романтическая история Элизабет Беннет и мистера Дарси.",
            "category": "Романы",
            "duration_seconds": 43200,  # 12 часов
            "is_free": True
        },
        {
            "title": "Психология влияния",
            "author": "Роберт Чалдини",
            "description": "Как понимать и использовать принципы психологического воздействия.",
            "category": "Психология",
            "duration_seconds": 27000,  # 7.5 часов
            "is_free": False
        }
    ]
    
    created_count = 0
    for book_data in demo_books:
        # Проверяем, существует ли книга
        existing = db.query(Book).filter(
            Book.title == book_data["title"],
            Book.author == book_data["author"]
        ).first()
        
        if not existing:
            category = categories.get(book_data["category"])
            
            book = Book(
                title=book_data["title"],
                author=book_data["author"],
                description=book_data["description"],
                duration_seconds=book_data["duration_seconds"],
                category_id=category.id if category else None,
                is_free=book_data["is_free"],
                added_by_admin_id=admin.id,
                # Для демо не добавляем реальные аудиофайлы
                audio_file_url=None,
                cover_url=None,
                rating=round(4.0 + (created_count * 0.2), 1),  # Рейтинги от 4.0 до 5.6
                plays_count=created_count * 15  # Разное количество прослушиваний
            )
            
            db.add(book)
            created_count += 1
            print(f"  ✅ Создана книга: {book.title} - {book.author}")
        else:
            print(f"  ⚠️  Книга уже существует: {book_data['title']}")
    
    db.commit()
    print(f"📊 Создано {created_count} новых книг")
    return created_count

def update_categories_count(db: Session):
    """Обновление счетчиков книг в категориях"""
    print("🔢 Обновляем счетчики книг в категориях...")
    
    categories = db.query(Category).all()
    for category in categories:
        books_count = db.query(Book).filter(
            Book.category_id == category.id,
            Book.is_active == True
        ).count()
        category.books_count = books_count
        print(f"  📚 {category.emoji} {category.name}: {books_count} книг")
    
    db.commit()

def main():
    """Основная функция"""
    print("🚀 Запуск создания демо-данных для BooksMood")
    print("=" * 50)
    
    try:
        # Создаем сессию БД
        db = SessionLocal()
        
        # Создаем таблицы если не существуют
        Base.metadata.create_all(bind=engine)
        
        # Создаем демо-данные
        categories_created = create_demo_categories(db)
        books_created = create_demo_books(db)
        update_categories_count(db)
        
        print("\n" + "=" * 50)
        print("✅ Демо-данные успешно созданы!")
        print(f"📚 Категорий создано: {categories_created}")
        print(f"📖 Книг создано: {books_created}")
        print("🎉 Система готова к использованию!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании демо-данных: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 