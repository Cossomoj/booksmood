#!/bin/bash
set -e

echo "🚀 Настройка директорий BooksMood на VPS"
echo "========================================"

# Создаем необходимые директории
echo "📁 Создание директорий на VPS..."
sudo mkdir -p /opt/booksmood-data
sudo mkdir -p /opt/booksmood-uploads
sudo mkdir -p /opt/booksmood-logs
sudo mkdir -p /opt/ssl-certs

# Устанавливаем правильные права
echo "🔐 Настройка прав доступа..."
sudo chown -R 1000:1000 /opt/booksmood-data
sudo chown -R 1000:1000 /opt/booksmood-uploads
sudo chown -R 1000:1000 /opt/booksmood-logs
sudo chmod 755 /opt/booksmood-data
sudo chmod 755 /opt/booksmood-uploads
sudo chmod 755 /opt/booksmood-logs

# Проверяем существующие volumes и мигрируем данные
echo "🔄 Проверка существующих данных..."

# Останавливаем контейнер если запущен
if sudo docker ps | grep -q booksmood_app; then
    echo "⏹️  Остановка контейнера..."
    sudo docker stop booksmood_app || true
fi

# Мигрируем данные из старых volumes если они существуют
if sudo docker volume ls | grep -q "booksmood_database"; then
    echo "📦 Миграция базы данных..."
    sudo docker run --rm -v booksmood_database:/from -v /opt/booksmood-data:/to alpine ash -c "cd /from ; cp -av . /to"
fi

if sudo docker volume ls | grep -q "booksmood_files"; then
    echo "📦 Миграция файлов..."
    sudo docker run --rm -v booksmood_files:/from -v /opt/booksmood-uploads:/to alpine ash -c "cd /from ; cp -av . /to"
fi

if sudo docker volume ls | grep -q "booksmood_logs"; then
    echo "📦 Миграция логов..."
    sudo docker run --rm -v booksmood_logs:/from -v /opt/booksmood-logs:/to alpine ash -c "cd /from ; cp -av . /to"
fi

# Информация о созданных директориях
echo ""
echo "✅ Директории созданы успешно:"
echo "   📂 /opt/booksmood-data     - База данных SQLite"
echo "   📂 /opt/booksmood-uploads  - Аудиофайлы и обложки"
echo "   📂 /opt/booksmood-logs     - Логи приложения"
echo "   📂 /opt/ssl-certs          - SSL сертификаты"
echo ""
echo "📊 Размер данных:"
du -sh /opt/booksmood-* 2>/dev/null || echo "   (данных пока нет)"
echo ""
echo "🎯 Следующий шаг: обновите docker-compose.yml и перезапустите контейнер"
echo "   wget -O docker-compose.yml https://raw.githubusercontent.com/Cossomoj/booksmood/main/docker-compose.yml"
echo "   sudo docker-compose up --build -d" 