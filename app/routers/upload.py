from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import aiofiles
from mutagen import File as MutagenFile
from PIL import Image
import shutil

from ..database import get_db
from ..schemas import BookCreate, BookResponse, StatusResponse
from ..models import Book, Admin
from ..dependencies import get_current_admin
from ..config import settings
from ..utils import ensure_directory_exists

router = APIRouter(prefix="/api/admin/upload", tags=["upload"])

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".aac", ".flac"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AUDIO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB

def get_file_extension(filename: str) -> str:
    """Получение расширения файла"""
    return os.path.splitext(filename.lower())[1]

def validate_audio_file(file: UploadFile) -> None:
    """Валидация аудиофайла"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Не указано имя файла")
    
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат аудио. Поддерживаются: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )
    
    if file.size and file.size > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер аудиофайла превышает {MAX_AUDIO_SIZE // (1024*1024)}MB"
        )

def validate_image_file(file: UploadFile) -> None:
    """Валидация изображения"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Не указано имя файла")
    
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат изображения. Поддерживаются: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    if file.size and file.size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер изображения превышает {MAX_IMAGE_SIZE // (1024*1024)}MB"
        )

async def save_uploaded_file(file: UploadFile, directory: str, filename: str) -> str:
    """Сохранение загруженного файла"""
    ensure_directory_exists(directory)
    file_path = os.path.join(directory, filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return file_path

def get_audio_duration(file_path: str) -> Optional[int]:
    """Получение длительности аудиофайла в секундах"""
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is not None and audio_file.info:
            return int(audio_file.info.length)
    except Exception:
        pass
    return None

def process_cover_image(file_path: str, output_path: str) -> None:
    """Обработка обложки: изменение размера и оптимизация"""
    try:
        with Image.open(file_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Изменяем размер, сохраняя пропорции
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Сохраняем с оптимизацией
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            
        # Удаляем исходный файл если он отличается
        if file_path != output_path:
            os.remove(file_path)
            
    except Exception as e:
        # Если обработка не удалась, оставляем исходный файл
        if file_path != output_path and os.path.exists(file_path):
            shutil.move(file_path, output_path)

@router.post("/audio", response_model=dict)
async def upload_audio(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin)
):
    """Загрузка аудиофайла"""
    validate_audio_file(file)
    
    # Генерируем уникальное имя файла
    file_extension = get_file_extension(file.filename)
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # Определяем путь для сохранения
    audio_dir = os.path.join(settings.upload_dir, "audio")
    file_path = await save_uploaded_file(file, audio_dir, unique_filename)
    
    # Получаем длительность аудио
    duration_seconds = get_audio_duration(file_path)
    
    # Формируем URL для доступа к файлу
    audio_url = f"/static/uploads/audio/{unique_filename}"
    
    return {
        "audio_url": audio_url,
        "duration_seconds": duration_seconds,
        "filename": unique_filename,
        "original_filename": file.filename
    }

@router.post("/cover", response_model=dict)
async def upload_cover(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin)
):
    """Загрузка обложки книги"""
    validate_image_file(file)
    
    # Генерируем уникальное имя файла
    unique_filename = f"{uuid.uuid4().hex}.jpg"
    
    # Определяем пути для сохранения
    covers_dir = os.path.join(settings.upload_dir, "covers")
    temp_path = await save_uploaded_file(file, covers_dir, f"temp_{unique_filename}")
    final_path = os.path.join(covers_dir, unique_filename)
    
    # Обрабатываем изображение
    process_cover_image(temp_path, final_path)
    
    # Формируем URL для доступа к файлу
    cover_url = f"/static/uploads/covers/{unique_filename}"
    
    return {
        "cover_url": cover_url,
        "filename": unique_filename,
        "original_filename": file.filename
    }

@router.post("/book", response_model=BookResponse)
async def create_book_with_files(
    title: str = Form(...),
    author: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    is_free: bool = Form(True),
    audio_file: UploadFile = File(...),
    cover_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Создание книги с загрузкой файлов"""
    
    # Загружаем аудиофайл
    validate_audio_file(audio_file)
    audio_extension = get_file_extension(audio_file.filename)
    audio_filename = f"{uuid.uuid4().hex}{audio_extension}"
    audio_dir = os.path.join(settings.upload_dir, "audio")
    audio_path = await save_uploaded_file(audio_file, audio_dir, audio_filename)
    audio_url = f"/static/uploads/audio/{audio_filename}"
    
    # Получаем длительность аудио
    duration_seconds = get_audio_duration(audio_path)
    
    # Загружаем обложку если предоставлена
    cover_url = None
    if cover_file and cover_file.filename:
        validate_image_file(cover_file)
        cover_filename = f"{uuid.uuid4().hex}.jpg"
        covers_dir = os.path.join(settings.upload_dir, "covers")
        temp_cover_path = await save_uploaded_file(cover_file, covers_dir, f"temp_{cover_filename}")
        final_cover_path = os.path.join(covers_dir, cover_filename)
        process_cover_image(temp_cover_path, final_cover_path)
        cover_url = f"/static/uploads/covers/{cover_filename}"
    
    # Создаем запись в базе данных
    book = Book(
        title=title,
        author=author,
        description=description,
        duration_seconds=duration_seconds,
        cover_url=cover_url,
        audio_file_url=audio_url,
        category_id=category_id,
        is_free=is_free,
        added_by_admin_id=current_admin.id
    )
    
    db.add(book)
    db.commit()
    db.refresh(book)
    
    return BookResponse.model_validate(book)

@router.delete("/file")
async def delete_file(
    file_url: str,
    current_admin: Admin = Depends(get_current_admin)
):
    """Удаление загруженного файла"""
    # Проверяем что это наш файл
    if not file_url.startswith("/static/uploads/"):
        raise HTTPException(status_code=400, detail="Неверный URL файла")
    
    # Получаем путь к файлу
    relative_path = file_url.replace("/static/uploads/", "")
    file_path = os.path.join(settings.upload_dir, relative_path)
    
    # Удаляем файл если он существует
    if os.path.exists(file_path):
        os.remove(file_path)
        return StatusResponse(status="success", message="Файл удален")
    else:
        raise HTTPException(status_code=404, detail="Файл не найден") 