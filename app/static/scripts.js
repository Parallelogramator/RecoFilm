document.addEventListener('DOMContentLoaded', () => {
    const dropdownLink = document.getElementById('library-link');
    const dropdownContent = document.querySelector('.dropdown-content');
    const modal = document.getElementById('movieModal');
    const modalBody = modal.querySelector('.modal-body');
    const modalClose = modal.querySelector('.modal-close');
    const searchForm = document.getElementById('searchForm');
    const limitSelector = document.getElementById('limit');
    const movieList = document.getElementById('movie-list');
    const noMoviesMessage = document.getElementById('no-movies-message');

    // Function to attach click handlers to movie cards
    function attachMovieCardHandlers() {
        document.querySelectorAll('.movie-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const movieId = card.dataset.movieId;
                const title = card.querySelector('.movie-title').textContent;
                const year = card.querySelector('.movie-year').textContent;
                const rating = card.querySelector('.movie-rating').textContent;
                const genres = Array.from(card.querySelectorAll('.genre-tag')).map(genre => genre.textContent);
                const statusTag = card.querySelector('.status-tag');
                const currentStatus = statusTag ? statusTag.textContent : '';
                const description = card.querySelector('.movie-description')?.textContent || 'No description';

                modalBody.innerHTML = `
                    <div class="movie-title">${title}</div>
                    <div class="movie-info">
                        <div class="movie-year">${year}</div>
                        <div class="movie-rating">${rating}</div>
                    </div>
                    <div class="movie-genres">
                        ${genres.map(genre => `<span class="genre-tag">${genre}</span>`).join('')}
                    </div>
                    ${statusTag ? `<span class="status-tag status-${currentStatus.toLowerCase().replace(/\s+/g, '-')}">${currentStatus}</span>` : ''}
                    <div class="status-selector">
                        <select>
                            <option value="">Выберите статус</option>
                            <option value="watched" ${currentStatus === 'watched' ? 'selected' : ''}>Watched</option>
                            <option value="liked" ${currentStatus === 'liked' ? 'selected' : ''}>Liked</option>
                            <option value="want_to_watch" ${currentStatus === 'want_to_watch' ? 'selected' : ''}>Want to watch</option>
                            <option value="dropped" ${currentStatus === 'dropped' ? 'selected' : ''}>Dropped</option>
                            <option value="watching" ${currentStatus === 'watching' ? 'selected' : ''}>Watching</option>
                        </select>
                    </div>
                    <div class="movie-description">${description}</div>
                `;

                modal.style.display = 'flex';

                const statusSelector = modalBody.querySelector('.status-selector select');
                statusSelector.addEventListener('change', async (e) => {
                    const newStatus = e.target.value;
                    const modalStatusTag = modalBody.querySelector('.status-tag');

                    if (modalStatusTag) {
                        modalStatusTag.textContent = newStatus;
                        modalStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                    } else {
                        const newStatusTag = document.createElement('span');
                        newMoviesTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                        newStatusTag.textContent = newStatus;
                        modalBody.querySelector('.movie-genres').insertAdjacentElement('afterend', newStatusTag);
                    }

                    const cardStatusTag = card.querySelector('.status-tag');
                    if (cardStatusTag) {
                        cardStatusTag.textContent = newStatus;
                        cardStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                    } else {
                        const newCardStatusTag = document.createElement('span');
                        newCardStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                        newCardStatusTag.textContent = newStatus;
                        card.querySelector('.movie-genres').insertAdjacentElement('afterend', newCardStatusTag);
                    }

                    try {
                        const response = await fetch('/users/1/interactions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ status: newStatus, movie_id: movieId })
                        });
                        if (!response.ok) {
                            console.error('Ошибка при добавлении статуса:', response.statusText);
                        }
                    } catch (error) {
                        console.error('Ошибка сети:', error);
                    }
                });
            });
        });
    }

    // Function to fetch and render movies
    async function fetchAndRenderMovies() {
        const queryParams = new URLSearchParams(window.location.search);
        const limit = limitSelector ? limitSelector.value : '10';
        queryParams.set('limit', limit);

        const isRecommendationsPage = window.location.pathname.includes('/recommendations');
        const endpoint = isRecommendationsPage ? '/api/recommendations' : '/api/movies';
        const url = `${endpoint}?${queryParams.toString()}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const movies = await response.json();

            // Clear existing movie list and message
            if (movieList) {
                movieList.innerHTML = '';
            }
            if (noMoviesMessage) {
                noMoviesMessage.style.display = 'none';
            }

            // Render movies or show no movies message
            if (movies.length > 0) {
                movies.forEach(movie => {
                    const li = document.createElement('li');
                    li.className = 'movie-card';
                    li.dataset.movieId = movie.id;
                    li.innerHTML = `
                        <div class="movie-title">${movie.title}</div>
                        <div class="movie-info">
                            <div class="movie-year">Year: ${movie.year || 'unspecified'}</div>
                            <div class="movie-rating">IMDB: ${movie.rating_imdb || 'unspecified'}</div>
                        </div>
                        <div class="movie-genres">
                            ${movie.genres.map(genre => `<span class="genre-tag">${genre}</span>`).join('')}
                        </div>
                        ${movie.status ? `<span class="status-tag status-${movie.status.value.toLowerCase().replace(/\s+/g, '-')}">${movie.status.value}</span>` : ''}
                        <div class="movie-description" style="display: none;">${movie.description || 'No description'}</div>
                    `;
                    movieList.appendChild(li);
                });
                attachMovieCardHandlers();
            } else {
                if (noMoviesMessage) {
                    noMoviesMessage.style.display = 'block';
                } else {
                    const p = document.createElement('p');
                    p.id = 'no-movies-message';
                    p.textContent = isRecommendationsPage ? 'Recommendations are not yet available.' : 'No movies are available yet. Add a movie via API!';
                    movieList.parentElement.insertBefore(p, movieList);
                }
            }
        } catch (error) {
            console.error('Ошибка при загрузке фильмов:', error);
            if (noMoviesMessage) {
                noMoviesMessage.textContent = 'Error loading movies. Please try again.';
                noMoviesMessage.style.display = 'block';
            }
        }
    }

    // Обработка отправки формы поиска
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const nameInput = document.getElementById('name').value.trim();
            const yearInput = document.getElementById('year').value.trim();
            const queryParams = new URLSearchParams();
            queryParams.set('name', nameInput);
            if (yearInput) {
                queryParams.set('year', yearInput);
            }
            if (limitSelector) {
                queryParams.set('limit', limitSelector.value);
            }
            // Update URL without reloading
            window.history.pushState({}, '', `${window.location.pathname}?${queryParams.toString()}`);
            fetchAndRenderMovies();
        });
    }

    // Обработка изменения количества отображаемых карточек
    if (limitSelector) {
        limitSelector.addEventListener('change', () => {
            const queryParams = new URLSearchParams(window.location.search);
            queryParams.set('limit', limitSelector.value);
            window.history.pushState({}, '', `${window.location.pathname}?${queryParams.toString()}`);
            fetchAndRenderMovies();
        });
    }

    // Открытие/закрытие меню по клику
    dropdownLink.addEventListener('click', (e) => {
        e.preventDefault();
        dropdownContent.classList.toggle('active');
    });

    // Закрытие меню при клике вне его
    document.addEventListener('click', (e) => {
        if (!dropdownLink.contains(e.target) && !dropdownContent.contains(e.target)) {
            dropdownContent.classList.remove('active');
        }
    });

    // Закрытие модального окна
    modalClose.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Закрытие модального окна при клике вне контента
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Initial attachment of movie card handlers
    attachMovieCardHandlers();
});

const themeToggle = document.querySelector('.theme-toggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
});