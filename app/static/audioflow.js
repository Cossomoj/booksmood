class AudioFlowApp {
    constructor() {
        this.currentUser = null;
        this.audioPlayer = null;
        this.currentBook = null;
        this.books = [];
        this.categories = [];
        this.progressUpdateTimer = null;
        this.playbackRate = 1.0;
        this.bookmarks = [];
        
        this.init();
    }

    async init() {
        console.log('Initializing AudioFlow...');
        
        // Инициализация Telegram WebApp
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }

        // Авторизация пользователя
        await this.authenticateUser();
        
        // Загрузка данных
        await this.loadCategories();
        await this.loadBooks();
        
        // Инициализация компонентов
        this.initAudioPlayer();
        this.initEventListeners();
        
        console.log('AudioFlow initialized successfully');
    }

    async authenticateUser() {
        try {
            // Проверяем доступность Telegram WebApp
            const tg = window.Telegram?.WebApp;
            let authResult = null;

            if (tg && tg.initData) {
                console.log('Telegram Web App detected, using real auth');
                // Реальная авторизация через Telegram
                const response = await fetch('/api/auth/telegram', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ initData: tg.initData })
                });

                if (response.ok) {
                    authResult = await response.json();
                } else {
                    const error = await response.json();
                    console.error('Telegram auth failed:', error);
                    
                    // Пробуем тестовую авторизацию в режиме разработки
                    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                        console.log('Trying test auth for development');
                        authResult = await this.testAuth();
                    }
                }
            } else {
                console.log('Telegram Web App not available, using test auth');
                // Используем тестовую авторизацию для разработки
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    authResult = await this.testAuth();
                } else {
                    console.warn('No Telegram WebApp data and not in development mode');
                    return;
                }
            }

            if (authResult) {
                this.currentUser = authResult.user;
                localStorage.setItem('access_token', authResult.access_token);
                console.log('User authenticated:', this.currentUser);
                
                // Уведомляем Telegram о готовности
                if (tg) {
                    tg.ready();
                    tg.MainButton.hide();
                }
            }
        } catch (error) {
            console.error('Authentication failed:', error);
        }
    }

    async testAuth() {
        """Тестовая авторизация для разработки"""
        try {
            const response = await fetch('/api/auth/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Test auth successful:', data.user);
                return data;
            } else {
                console.error('Test auth failed:', response.status);
                return null;
            }
        } catch (error) {
            console.error('Test auth error:', error);
            return null;
        }
    }

    async loadCategories() {
        try {
            const response = await this.apiCall('/api/categories');
            if (response) {
                this.categories = response;
                this.renderCategories();
            }
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    async loadBooks(categoryId = null, limit = 20, offset = 0) {
        try {
            let url = `/api/books?limit=${limit}&offset=${offset}`;
            if (categoryId) {
                url += `&category_id=${categoryId}`;
            }

            const response = await this.apiCall(url);
            if (response) {
                this.books = response.books;
                this.renderBooks();
            }
        } catch (error) {
            console.error('Failed to load books:', error);
        }
    }

    // Обновляем метод API вызовов для лучшей обработки ошибок
    async apiCall(url, options = {}) {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.ok) {
                const data = await response.json();
                return data;
            } else if (response.status === 401) {
                // Токен истек, пробуем переавторизоваться
                console.log('Token expired, trying to re-authenticate');
                localStorage.removeItem('access_token');
                this.currentUser = null;
                await this.authenticateUser();
                
                // Повторяем запрос с новым токеном
                if (this.currentUser) {
                    const newToken = localStorage.getItem('access_token');
                    headers['Authorization'] = `Bearer ${newToken}`;
                    const retryResponse = await fetch(url, { ...options, headers });
                    if (retryResponse.ok) {
                        return await retryResponse.json();
                    }
                }
                return null;
            } else {
                console.error('API call failed:', response.status, response.statusText);
                return null;
            }
        } catch (error) {
            console.error('Network error:', error);
            return null;
        }
    }

    renderCategories() {
        const container = document.querySelector('.categories');
        if (!container) return;

        const allChip = `<div class="category-chip active" data-category-id="">Все</div>`;
        const categoryChips = this.categories.map(category => `
            <div class="category-chip" data-category-id="${category.id}">
                ${category.emoji || '📁'} ${category.name} ${category.books_count > 0 ? `(${category.books_count})` : ''}
            </div>
        `).join('');

        container.innerHTML = allChip + categoryChips;

        // Добавляем обработчики событий
        container.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                container.querySelector('.category-chip.active')?.classList.remove('active');
                chip.classList.add('active');
                
                const categoryId = chip.dataset.categoryId || null;
                const categoryName = categoryId ? chip.textContent.split('(')[0].trim() : 'Все книги';
                
                this.loadBooks(categoryId);
                
                // Обновляем заголовок секции
                const popularTitle = document.querySelector('.section-title');
                if (popularTitle) {
                    popularTitle.textContent = categoryName;
                }
                
                // Очищаем поиск
                const searchInput = document.querySelector('.search-input');
                if (searchInput) {
                    searchInput.value = '';
                }
            });
        });
    }

    renderBooks() {
        this.renderFeaturedBook();
        this.renderRecentBooks();
        this.renderNewBooks();
    }

    renderFeaturedBook() {
        if (this.books.length === 0) {
            // Показываем плейсхолдер если нет книг
            const container = document.querySelector('.featured-card');
            if (container) {
                container.innerHTML = `
                    <div class="featured-cover" style="background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 48px;">📚</div>
                    <div class="featured-content">
                        <h3 class="featured-title">Добро пожаловать в AudioFlow</h3>
                        <p class="featured-author">Загрузите первую книгу через админ панель</p>
                        <div class="featured-stats">
                            <div class="stat-item">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                                </svg>
                                <span>Библиотека пуста</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            return;
        }
        
        const featured = this.books[0];
        const container = document.querySelector('.featured-card');
        if (!container) return;

        const duration = this.formatDuration(featured.duration_seconds);
        const progress = featured.user_progress?.current_position || 0;
        const total = featured.duration_seconds || 0;
        const progressPercent = total > 0 ? Math.round((progress / total) * 100) : 0;

        container.innerHTML = `
            <div class="featured-cover" style="background-image: url('${featured.cover_url || ''}')"></div>
            <div class="featured-content">
                <h3 class="featured-title">${featured.title}</h3>
                <p class="featured-author">${featured.author}</p>
                <p style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">
                    ${featured.description || 'Описание недоступно'}
                </p>
                <div class="featured-stats">
                    <div class="stat-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                        </svg>
                        <span>${featured.is_free ? 'Бесплатно' : 'Премиум'}</span>
                    </div>
                    <div class="stat-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        <span>${duration}</span>
                    </div>
                    <div class="stat-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
                        </svg>
                        <span>${featured.rating.toFixed(1)}</span>
                    </div>
                </div>
                ${progressPercent > 0 ? `
                    <div class="progress-bar" style="margin-top: 12px;">
                        <div class="progress-fill" style="width: ${progressPercent}%"></div>
                    </div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                        Прослушано ${progressPercent}%
                    </div>
                ` : ''}
                <button class="featured-play-btn" onclick="audioFlow.playBook(${featured.id})">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                    ${progressPercent > 0 ? 'Продолжить' : 'Слушать'}
                </button>
            </div>
        `;
    }

    renderRecentBooks() {
        const container = document.querySelector('.books-scroll');
        if (!container) return;

        const recentBooks = this.books.filter(book => 
            book.user_progress?.current_position > 0
        ).slice(0, 5);

        if (recentBooks.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">Начните слушать первую книгу!</p>';
            return;
        }

        container.innerHTML = recentBooks.map(book => this.renderBookCard(book, 'horizontal')).join('');
    }

    renderNewBooks() {
        const container = document.querySelector('.books-grid');
        if (!container) return;

        const newBooks = this.books
            .filter(book => !book.user_progress?.current_position)
            .slice(0, 6);

        if (newBooks.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px; grid-column: 1 / -1;">Нет доступных книг</p>';
            return;
        }

        container.innerHTML = newBooks.map(book => this.renderBookCard(book, 'grid')).join('');
    }

    initAudioPlayer() {
        this.audioPlayer = document.createElement('audio');
        this.audioPlayer.preload = 'metadata';
        
        // События аудиоплеера
        this.audioPlayer.addEventListener('loadedmetadata', () => {
            this.updatePlayerUI();
        });

        this.audioPlayer.addEventListener('timeupdate', () => {
            this.updateProgress();
        });

        this.audioPlayer.addEventListener('ended', () => {
            this.onAudioEnded();
        });

        this.audioPlayer.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            this.showError('Ошибка воспроизведения аудио');
        });
    }

    async playBook(bookId) {
        try {
            // Получаем информацию о книге
            const book = this.books.find(b => b.id === bookId);
            if (!book) {
                // Пытаемся получить информацию о книге из API
                const bookData = await this.apiCall(`/api/books/${bookId}`);
                if (!bookData) {
                    console.error('Book not found:', bookId);
                    this.showError('Книга не найдена');
                    return;
                }
                this.currentBook = bookData;
            } else {
                this.currentBook = book;
            }

            // Получаем прогресс пользователя если авторизован
            let progress = { current_position: 0, total_duration: this.currentBook.duration_seconds };
            try {
                const progressData = await this.apiCall(`/api/user/history/${bookId}`);
                if (progressData) {
                    progress = progressData;
                }
            } catch (error) {
                console.log('No user progress available (not authenticated)');
            }
            
            this.currentBook.progress = progress;

            // Загружаем аудио через новый API
            this.audioPlayer.src = `/api/books/${bookId}/audio`;
            this.audioPlayer.currentTime = this.currentBook.progress.current_position;

            // Показываем плеер
            this.showPlayer();
            
            // Автовоспроизведение
            await this.audioPlayer.play();
            
            console.log('Playing book:', this.currentBook.title);
        } catch (error) {
            console.error('Failed to play book:', error);
            this.showError('Не удалось воспроизвести книгу: ' + error.message);
        }
    }

    showPlayer() {
        if (!this.currentBook) return;

        // Создаем интерфейс плеера если он не существует
        let player = document.querySelector('.audio-player');
        if (!player) {
            player = document.createElement('div');
            player.className = 'audio-player';
            document.body.appendChild(player);
        }

        player.innerHTML = `
            <div class="player-content">
                <div class="player-book-info">
                    <div class="player-cover" style="background-image: url('${this.currentBook.cover_url || ''}')"></div>
                    <div class="player-text">
                        <div class="player-title">${this.currentBook.title}</div>
                        <div class="player-author">${this.currentBook.author}</div>
                    </div>
                </div>
                <div class="player-controls">
                    <button class="player-btn" onclick="audioFlow.seek(-30)">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 4v6h6M23 20v-6h-6"></path>
                            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                        </svg>
                        -30
                    </button>
                    <button class="player-btn player-play-btn" onclick="audioFlow.togglePlayPause()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                    </button>
                    <button class="player-btn" onclick="audioFlow.seek(30)">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6M1 20v-6h6"></path>
                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                        </svg>
                        +30
                    </button>
                    <button class="player-btn" onclick="audioFlow.togglePlaybackRate()" title="Скорость воспроизведения">
                        <span class="playback-rate">${this.playbackRate}x</span>
                    </button>
                    <button class="player-btn" onclick="audioFlow.addBookmark()" title="Добавить закладку">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"></path>
                        </svg>
                    </button>
                    <button class="player-btn" onclick="audioFlow.showBookmarks()" title="Закладки">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                        </svg>
                    </button>
                </div>
                <div class="player-progress">
                    <div class="player-time">
                        <span class="current-time">0:00</span>
                        <span class="total-time">${this.formatDuration(this.currentBook.duration_seconds)}</span>
                    </div>
                    <div class="progress-bar-container" onclick="audioFlow.seekToPosition(event)">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        player.classList.add('show');
    }

    togglePlayPause() {
        if (!this.audioPlayer || !this.currentBook) return;

        if (this.audioPlayer.paused) {
            this.audioPlayer.play();
        } else {
            this.audioPlayer.pause();
        }

        this.updatePlayerUI();
    }

    seek(seconds) {
        if (!this.audioPlayer) return;
        
        this.audioPlayer.currentTime = Math.max(0, 
            Math.min(this.audioPlayer.duration, this.audioPlayer.currentTime + seconds)
        );
    }

    seekToPosition(event) {
        if (!this.audioPlayer || !this.audioPlayer.duration) return;

        const rect = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const percentage = x / rect.width;
        
        this.audioPlayer.currentTime = percentage * this.audioPlayer.duration;
    }

    updatePlayerUI() {
        const playBtn = document.querySelector('.player-play-btn svg');
        if (!playBtn) return;

        if (this.audioPlayer.paused) {
            playBtn.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
        } else {
            playBtn.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
        }
    }

    updateProgress() {
        if (!this.audioPlayer || !this.currentBook) return;

        const currentTime = this.audioPlayer.currentTime;
        const duration = this.audioPlayer.duration || this.currentBook.duration_seconds;

        // Обновляем UI
        const currentTimeEl = document.querySelector('.current-time');
        const progressFill = document.querySelector('.player-progress .progress-fill');

        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatDuration(currentTime);
        }

        if (progressFill && duration > 0) {
            const percentage = (currentTime / duration) * 100;
            progressFill.style.width = percentage + '%';
        }

        // Сохраняем прогресс каждые 30 секунд и только если позиция изменилась значительно
        const lastSavedTime = this.lastSavedTime || 0;
        if (Math.floor(currentTime) % 30 === 0 && Math.abs(currentTime - lastSavedTime) > 5) {
            this.saveProgress();
            this.lastSavedTime = currentTime;
        }
    }

    async saveProgress() {
        if (!this.currentBook || !this.audioPlayer) return;

        const position = Math.floor(this.audioPlayer.currentTime);
        const duration = Math.floor(this.audioPlayer.duration || this.currentBook.duration_seconds);

        try {
            await this.apiCall(`/api/user/history/${this.currentBook.id}`, {
                method: 'POST',
                body: JSON.stringify({
                    position: position,
                    duration: duration
                })
            });
            console.log(`Progress saved: ${position}s / ${duration}s`);
        } catch (error) {
            // Не показываем ошибку пользователю если он не авторизован
            console.log('Failed to save progress (user may not be authenticated):', error);
        }
    }

    onAudioEnded() {
        // Отмечаем книгу как прослушанную
        if (this.currentBook) {
            this.apiCall(`/api/user/history/${this.currentBook.id}/finish`, {
                method: 'POST'
            });
        }

        // Можно добавить логику для автоматического перехода к следующей книге
        console.log('Audio ended');
    }

    formatDuration(seconds) {
        if (!seconds) return '0:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        }
    }

    showError(message) {
        // Показываем уведомление об ошибке
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    togglePlaybackRate() {
        // Переключение скорости воспроизведения: 0.75x, 1x, 1.25x, 1.5x, 2x
        const rates = [0.75, 1.0, 1.25, 1.5, 2.0];
        const currentIndex = rates.indexOf(this.playbackRate);
        const nextIndex = (currentIndex + 1) % rates.length;
        
        this.playbackRate = rates[nextIndex];
        if (this.audioPlayer) {
            this.audioPlayer.playbackRate = this.playbackRate;
        }
        
        // Обновляем отображение скорости
        const rateBtn = document.querySelector('.playback-rate');
        if (rateBtn) {
            rateBtn.textContent = this.playbackRate + 'x';
        }
        
        // Сохраняем в localStorage
        localStorage.setItem('playbackRate', this.playbackRate.toString());
    }

    async addBookmark() {
        if (!this.currentBook || !this.audioPlayer) return;
        
        const position = Math.floor(this.audioPlayer.currentTime);
        const title = prompt('Название закладки:', `Глава ${Math.floor(position / 600) + 1}`);
        
        if (title === null) return; // Пользователь отменил
        
        try {
            const response = await this.apiCall(`/api/user/bookmarks/${this.currentBook.id}`, {
                method: 'POST',
                body: JSON.stringify({
                    position: position,
                    title: title || `Закладка ${this.formatDuration(position)}`
                })
            });
            
            if (response) {
                this.showNotification('Закладка добавлена!', 'success');
                this.loadBookmarks();
            }
        } catch (error) {
            console.error('Failed to add bookmark:', error);
            this.showError('Не удалось добавить закладку');
        }
    }

    async loadBookmarks() {
        if (!this.currentBook) return;
        
        try {
            const response = await this.apiCall(`/api/user/bookmarks/${this.currentBook.id}`);
            if (response) {
                this.bookmarks = response;
            }
        } catch (error) {
            console.error('Failed to load bookmarks:', error);
        }
    }

    showBookmarks() {
        if (!this.currentBook || this.bookmarks.length === 0) {
            this.showError('Нет закладок для этой книги');
            return;
        }
        
        // Создаем модальное окно с закладками
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8); display: flex; align-items: center;
            justify-content: center; z-index: 1001;
        `;
        
        modal.innerHTML = `
            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; width: 90%; max-width: 400px; max-height: 70vh; overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="color: var(--text-primary); margin: 0;">Закладки</h3>
                    <button onclick="this.closest('div').remove()" style="background: none; border: none; color: var(--text-secondary); font-size: 24px; cursor: pointer;">&times;</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    ${this.bookmarks.map(bookmark => `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: var(--border); border-radius: 8px;">
                            <div onclick="audioFlow.seekToBookmark(${bookmark.position})" style="cursor: pointer; flex: 1;">
                                <div style="color: var(--text-primary); font-weight: 500;">${bookmark.title}</div>
                                <div style="color: var(--text-secondary); font-size: 12px;">${this.formatDuration(bookmark.position)}</div>
                            </div>
                            <button onclick="audioFlow.deleteBookmark(${bookmark.id})" style="background: var(--accent); border: none; color: white; padding: 5px 8px; border-radius: 4px; cursor: pointer; font-size: 12px;">Удалить</button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    seekToBookmark(position) {
        if (this.audioPlayer) {
            this.audioPlayer.currentTime = position;
            // Закрываем модальное окно
            document.querySelector('[style*="rgba(0,0,0,0.8)"]')?.remove();
        }
    }

    async deleteBookmark(bookmarkId) {
        try {
            const response = await this.apiCall(`/api/user/bookmarks/${bookmarkId}`, {
                method: 'DELETE'
            });
            
            if (response) {
                this.showNotification('Закладка удалена', 'success');
                this.loadBookmarks();
                // Закрываем модальное окно и показываем обновленный список
                document.querySelector('[style*="rgba(0,0,0,0.8)"]')?.remove();
                setTimeout(() => this.showBookmarks(), 100);
            }
        } catch (error) {
            console.error('Failed to delete bookmark:', error);
            this.showError('Не удалось удалить закладку');
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            padding: 12px 20px; border-radius: 8px; color: white;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    initEventListeners() {
        // Поиск
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query === '') {
                    // Если поиск очищен, возвращаемся к обычному списку
                    this.loadBooks();
                    const popularTitle = document.querySelector('.section-title');
                    if (popularTitle) {
                        popularTitle.textContent = 'Популярные';
                    }
                    return;
                }
                
                searchTimeout = setTimeout(() => {
                    this.searchBooks(query);
                }, 500); // Увеличил задержку для уменьшения нагрузки
            });
            
            // Обработка Enter
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    clearTimeout(searchTimeout);
                    this.searchBooks(e.target.value);
                }
            });
        }
    }

    async searchBooks(query) {
        if (!query.trim()) {
            this.loadBooks();
            return;
        }

        if (query.length < 2) {
            return; // Минимум 2 символа для поиска
        }

        try {
            const response = await this.apiCall(`/api/books/search?q=${encodeURIComponent(query)}&limit=20`);
            if (response) {
                this.books = response.books;
                this.renderBooks();
                
                // Обновляем заголовок секции
                const popularTitle = document.querySelector('.section-title');
                if (popularTitle) {
                    popularTitle.textContent = `Результаты поиска "${query}" (${response.total})`;
                }
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.showError('Ошибка поиска');
        }
    }

    // Добавляем функции для работы с избранным
    async toggleFavorite(bookId) {
        try {
            // Сначала проверяем текущий статус
            const statusResponse = await this.apiCall(`/api/user/favorites/${bookId}/status`);
            
            if (statusResponse && statusResponse.is_favorite) {
                // Удаляем из избранного
                const response = await this.apiCall(`/api/user/favorites/${bookId}`, {
                    method: 'DELETE'
                });
                
                if (response && response.status === 'success') {
                    this.showNotification('Удалено из избранного', 'success');
                    this.updateFavoriteButton(bookId, false);
                    return false;
                }
            } else {
                // Добавляем в избранное
                const response = await this.apiCall(`/api/user/favorites/${bookId}`, {
                    method: 'POST'
                });
                
                if (response && response.status === 'success') {
                    this.showNotification(response.message || 'Добавлено в избранное', 'success');
                    this.updateFavoriteButton(bookId, true);
                    return true;
                } else if (response && response.status === 'already_exists') {
                    this.showNotification('Книга уже в избранном', 'info');
                    this.updateFavoriteButton(bookId, true);
                    return true;
                }
            }
        } catch (error) {
            console.error('Failed to toggle favorite:', error);
            this.showError('Ошибка при изменении избранного');
        }
        return null;
    }

    updateFavoriteButton(bookId, isFavorite) {
        // Обновляем все кнопки избранного для этой книги
        const favoriteButtons = document.querySelectorAll(`[data-book-id="${bookId}"] .favorite-btn, .favorite-btn[data-book-id="${bookId}"]`);
        
        favoriteButtons.forEach(btn => {
            const icon = btn.querySelector('svg') || btn;
            if (isFavorite) {
                btn.classList.add('active');
                icon.innerHTML = `
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
                          fill="currentColor"/>
                `;
                btn.title = 'Удалить из избранного';
            } else {
                btn.classList.remove('active');
                icon.innerHTML = `
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
                          fill="none" stroke="currentColor" stroke-width="2"/>
                `;
                btn.title = 'Добавить в избранное';
            }
        });
    }

    async loadUserFavorites() {
        try {
            const response = await this.apiCall('/api/user/favorites?limit=20');
            if (response) {
                return response;
            }
        } catch (error) {
            console.error('Failed to load favorites:', error);
        }
        return [];
    }

    // Обновляем функцию рендеринга карточек книг для включения кнопки избранного
    renderBookCard(book, cardType = 'grid') {
        const progressPercent = book.user_progress ? 
            Math.round((book.user_progress.current_position / (book.duration_seconds || 1)) * 100) : 0;
        const isFavorite = book.user_progress?.is_favorite || false;
        const coverStyle = book.cover_url 
            ? `background-image: url('${book.cover_url}')` 
            : `background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)`;
        
        const favoriteIcon = isFavorite 
            ? `<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor"/>`
            : `<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="none" stroke="currentColor" stroke-width="2"/>`;

        if (cardType === 'horizontal') {
            return `
                <div class="book-card book-card-horizontal" data-book-id="${book.id}">
                    <div class="book-cover" style="${coverStyle}; background-size: cover; background-position: center;" onclick="audioFlow.playBook(${book.id})">
                        <div class="book-badge">${progressPercent}%</div>
                        <button class="favorite-btn ${isFavorite ? 'active' : ''}" 
                                onclick="event.stopPropagation(); audioFlow.toggleFavorite(${book.id})"
                                title="${isFavorite ? 'Удалить из избранного' : 'Добавить в избранное'}"
                                style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); border: none; color: #fbbf24; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                                ${favoriteIcon}
                            </svg>
                        </button>
                    </div>
                    <div class="book-info">
                        <div class="book-title">${book.title}</div>
                        <div class="book-author">${book.author}</div>
                    </div>
                </div>
            `;
        } else {
            const badge = book.is_free ? 'Бесплатно' : 'Премиум';
            return `
                <div class="book-card" data-book-id="${book.id}">
                    <div class="book-cover" style="${coverStyle}; background-size: cover; background-position: center;" onclick="audioFlow.playBook(${book.id})">
                        <div class="book-badge">${badge}</div>
                        <button class="favorite-btn ${isFavorite ? 'active' : ''}" 
                                onclick="event.stopPropagation(); audioFlow.toggleFavorite(${book.id})"
                                title="${isFavorite ? 'Удалить из избранного' : 'Добавить в избранное'}"
                                style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); border: none; color: #fbbf24; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                                ${favoriteIcon}
                            </svg>
                        </button>
                    </div>
                    <div class="book-info">
                        <div class="book-title">${book.title}</div>
                        <div class="book-author">${book.author}</div>
                    </div>
                </div>
            `;
        }
    }
}

// Инициализация приложения
const audioFlow = new AudioFlowApp(); 