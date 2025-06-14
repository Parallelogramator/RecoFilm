document.addEventListener('DOMContentLoaded', () => {
    const dropdownLink = document.getElementById('library-link');
    const dropdownContent = document.querySelector('.dropdown-content');
    const modal = document.getElementById('movieModal');
    const modalBody = modal.querySelector('.modal-body');
    const modalClose = modal.querySelector('.modal-close');
    const limitSelector = document.getElementById('limit');
    const limitHiddenInput = document.getElementById('limit-hidden');
    const searchForm = document.getElementById('searchForm');

    // Обработка отправки формы поиска
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const nameInput = document.getElementById('name').value.trim();
            const yearInput = document.getElementById('year').value.trim();
            console.log('Name:', nameInput, 'Year:', yearInput);
            const queryParams = new URLSearchParams();
            queryParams.append('name', nameInput);
            if (yearInput) {
                queryParams.append('year', yearInput);
            }
            const searchUrl = `/search?${queryParams.toString()}`;
            console.log('Redirecting to:', searchUrl);
            window.location.href = searchUrl;
        });
    }

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
                        newStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
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

    // Sync hidden limit input with limit selector
    if (limitSelector && limitHiddenInput) {
        limitSelector.addEventListener('change', () => {
            limitHiddenInput.value = limitSelector.value;
        });
        // Initialize hidden input value
        limitHiddenInput.value = limitSelector.value;
    }

    // Обработка изменения количества отображаемых карточек
    if (limitSelector) {
        limitSelector.addEventListener('change', () => {
            const queryParams = new URLSearchParams(window.location.search);
            queryParams.set('limit', limitSelector.value);
            window.location.href = `${window.location.pathname}?${queryParams.toString()}`;
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