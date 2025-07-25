import os
import uuid
from typing import Optional
from PIL import Image
from mutagen.mp3 import MP3
from fastapi import UploadFile, HTTPException
import aiofiles

from .config import settings

async def save_uploaded_file(file: UploadFile, directory: str) -> str:
    """Сохранение загруженного файла"""
    # Проверка размера файла
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Создание директории если не существует
    full_directory = os.path.join(settings.upload_dir, directory)
    os.makedirs(full_directory, exist_ok=True)
    
    # Генерация уникального имени файла
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(full_directory, unique_filename)
    
    # Сохранение файла
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return f"/static/uploads/{directory}/{unique_filename}"

async def save_and_optimize_image(file: UploadFile, max_width: int = 500, max_height: int = 750) -> str:
    """Сохранение и оптимизация изображения"""
    # Проверка типа файла
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Сохранение файла
    cover_url = await save_uploaded_file(file, "covers")
    
    # Оптимизация изображения
    file_path = os.path.join(settings.upload_dir, "covers", os.path.basename(cover_url))
    
    try:
        with Image.open(file_path) as img:
            # Конвертация в RGB если необходимо
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Изменение размера с сохранением пропорций
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Сохранение с оптимизацией
            img.save(file_path, format='JPEG', optimize=True, quality=85)
            
    except Exception as e:
        # Удаляем файл если не удалось обработать
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
    
    return cover_url

async def save_audio_file(file: UploadFile) -> tuple[str, int]:
    """Сохранение аудиофайла и получение его длительности"""
    # Проверка типа файла
    if not file.content_type or file.content_type not in ['audio/mpeg', 'audio/mp3']:
        raise HTTPException(status_code=400, detail="Audio file must be MP3")
    
    # Сохранение файла
    audio_url = await save_uploaded_file(file, "audio")
    
    # Получение длительности
    file_path = os.path.join(settings.upload_dir, "audio", os.path.basename(audio_url))
    
    try:
        audio = MP3(file_path)
        duration_seconds = int(audio.info.length)
    except Exception as e:
        # Удаляем файл если не удалось обработать
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process audio file: {str(e)}")
    
    return audio_url, duration_seconds

def format_duration(seconds: int) -> str:
    """Форматирование длительности в читаемый вид"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}ч {minutes}м"
    else:
        return f"{minutes}м {seconds}с"

def calculate_progress_percent(current_position: int, total_duration: int) -> float:
    """Расчет процента прослушанности"""
    if total_duration <= 0:
        return 0.0
    return round((current_position / total_duration) * 100, 1)

def delete_file(file_path: str) -> bool:
    """Удаление файла"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False

def ensure_directory_exists(directory: str):
    """Создание директории если не существует"""
    os.makedirs(directory, exist_ok=True) 