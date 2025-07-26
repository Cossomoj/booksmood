class AudioFlowApp {
    constructor() {
        this.currentUser = null;
        this.audioPlayer = null;
        this.currentBook = null;
        this.books = [];
        this.categories = [];
        this.progressUpdateTimer = null;
        
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
            // Получаем initData из Telegram WebApp
            const initData = window.Telegram?.WebApp?.initData || '';
            
            if (!initData) {
                console.warn('No Telegram WebApp data available');
                return;
            }

            const response = await fetch('/api/auth/telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ initData })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                localStorage.setItem('access_token', data.access_token);
                console.log('User authenticated:', this.currentUser);
            }
        } catch (error) {
            console.error('Authentication failed:', error);
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
                return await response.json();
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

        container.innerHTML = `
            <div class="category-chip active" data-category-id="">Все</div>
            ${this.categories.map(category => `
                <div class="category-chip" data-category-id="${category.id}">
                    ${category.emoji || ''} ${category.name}
                </div>
            `).join('')}
        `;

        // Добавляем обработчики событий
        container.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                container.querySelector('.category-chip.active')?.classList.remove('active');
                chip.classList.add('active');
                
                const categoryId = chip.dataset.categoryId || null;
                this.loadBooks(categoryId);
            });
        });
    }

    renderBooks() {
        this.renderFeaturedBook();
        this.renderRecentBooks();
        this.renderNewBooks();
    }

    renderFeaturedBook() {
        if (this.books.length === 0) return;
        
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

        container.innerHTML = recentBooks.map(book => {
            const progress = book.user_progress?.current_position || 0;
            const total = book.duration_seconds || 0;
            const progressPercent = total > 0 ? Math.round((progress / total) * 100) : 0;

            return `
                <div class="book-card book-card-horizontal" onclick="audioFlow.playBook(${book.id})">
                    <div class="book-cover" style="background-image: url('${book.cover_url || ''}')">
                        <div class="book-badge">${progressPercent}%</div>
                    </div>
                    <div class="book-info">
                        <div class="book-title">${book.title}</div>
                        <div class="book-author">${book.author}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderNewBooks() {
        const container = document.querySelector('.books-grid');
        if (!container) return;

        const newBooks = this.books
            .filter(book => !book.user_progress?.current_position)
            .slice(0, 6);

        container.innerHTML = newBooks.map(book => `
            <div class="book-card" onclick="audioFlow.playBook(${book.id})">
                <div class="book-cover" style="background-image: url('${book.cover_url || ''}')">
                    <div class="book-badge">NEW</div>
                </div>
                <div class="book-info">
                    <div class="book-title">${book.title}</div>
                    <div class="book-author">${book.author}</div>
                </div>
            </div>
        `).join('');
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
                console.error('Book not found:', bookId);
                return;
            }

            // Получаем прогресс пользователя
            const progress = await this.apiCall(`/api/user/history/${bookId}`);
            
            this.currentBook = {
                ...book,
                progress: progress || { current_position: 0, total_duration: book.duration_seconds }
            };

            // Загружаем аудио
            this.audioPlayer.src = book.audio_file_url;
            this.audioPlayer.currentTime = this.currentBook.progress.current_position;

            // Показываем плеер
            this.showPlayer();
            
            // Автовоспроизведение
            await this.audioPlayer.play();
            
            console.log('Playing book:', book.title);
        } catch (error) {
            console.error('Failed to play book:', error);
            this.showError('Не удалось воспроизвести книгу');
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

        // Сохраняем прогресс каждые 10 секунд
        if (Math.floor(currentTime) % 10 === 0) {
            this.saveProgress();
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
        } catch (error) {
            console.error('Failed to save progress:', error);
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

    initEventListeners() {
        // Поиск
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchBooks(e.target.value);
                }, 300);
            });
        }
    }

    async searchBooks(query) {
        if (!query.trim()) {
            this.loadBooks();
            return;
        }

        try {
            const response = await this.apiCall(`/api/books/search?q=${encodeURIComponent(query)}`);
            if (response) {
                this.books = response.books;
                this.renderBooks();
            }
        } catch (error) {
            console.error('Search failed:', error);
        }
    }
}

// Инициализация приложения
const audioFlow = new AudioFlowApp(); 