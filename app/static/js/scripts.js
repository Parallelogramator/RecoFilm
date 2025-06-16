// Ожидание полной загрузки DOM перед выполнением скриптов
document.addEventListener('DOMContentLoaded', () => {
    // Получение элементов DOM
    const dropdownLink = document.getElementById('library-link'); // Ссылка на выпадающее меню "Library" (см. .dropdown в CSS)
    const dropdownContent = document.querySelector('.dropdown-content'); // Контент выпадающего меню (стили в .dropdown-content CSS)
    const modal = document.getElementById('movieModal'); // Модальное окно для фильма (стили в .modal CSS)
    const modalBody = modal.querySelector('.modal-body'); // Тело модального окна (стили в .modal-body CSS)
    const modalClose = modal.querySelector('.modal-close'); // Кнопка закрытия модального окна (стили в .modal-close CSS)
    const limitSelector = document.getElementById('limit'); // Селектор лимита отображения карточек (стили в .limit-selector CSS)
    const limitHiddenInput = document.getElementById('limit-hidden'); // Скрытое поле для лимита в форме поиска
    const searchForm = document.getElementById('searchForm'); // Форма поиска (стили в .search-form CSS)

    // Обработка отправки формы поиска
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault(); // Отмена стандартной отправки формы
            const nameInput = document.getElementById('name').value.trim(); // Значение поля "Название фильма" (см. .search-form .input-cell input[type="text"] в CSS)
            const yearInput = document.getElementById('year').value.trim(); // Значение поля "Год" (см. .search-form .input-cell input[type="number"] в CSS)

            // Формирование URL с параметрами поиска
            const queryParams = new URLSearchParams();
            queryParams.append('name', nameInput);
            if (yearInput) {
                queryParams.append('year', yearInput);
            }
            const searchUrl = `/search?${queryParams.toString()}&limit=10`; // URL с параметрами (лимит по умолчанию 10)

            // Перенаправление на страницу поиска
            window.location.href = searchUrl;
        });
    }

    // Функция для добавления обработчиков клика на карточки фильмов
    function attachMovieCardHandlers() {
        document.querySelectorAll('.movie-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Получение данных о фильме из карточки (см. .movie-card, .movie-title, .movie-year, .movie-rating, .genre-tag в CSS)
                const movieId = card.dataset.movieId; // ID фильма
                const title = card.querySelector('.movie-title').textContent; // Название фильма
                const year = card.querySelector('.movie-year').textContent; // Год выпуска
                const rating = card.querySelector('.movie-rating').textContent; // Рейтинг
                const genres = Array.from(card.querySelectorAll('.genre-tag')).map(genre => genre.textContent); // Жанры
                const statusTag = card.querySelector('.status-tag'); // Тег статуса (см. .status-tag в CSS)
                const currentStatus = statusTag ? statusTag.textContent : ''; // Текущий статус
                const description = card.querySelector('.movie-description')?.textContent || 'No description'; // Описание

                // Заполнение модального окна данными о фильме
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

                modal.style.display = 'flex'; // Отображение модального окна (см. .modal display: flex в CSS)

                // Обработчик изменения статуса фильма
                const statusSelector = modalBody.querySelector('.status-selector select'); // Селектор статуса (см. .status-selector select в CSS)
                statusSelector.addEventListener('change', async (e) => {
                    const newStatus = e.target.value; // Новый статус

                    // Обновление статуса в модальном окне
                    const modalStatusTag = modalBody.querySelector('.status-tag');
                    if (modalStatusTag) {
                        modalStatusTag.textContent = newStatus;
                        modalStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`; // Обновление класса (см. .status-tag в CSS)
                    } else {
                        const newStatusTag = document.createElement('span');
                        newStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                        newStatusTag.textContent = newStatus;
                        modalBody.querySelector('.movie-genres').insertAdjacentElement('afterend', newStatusTag);
                    }

                    // Обновление статуса в карточке фильма
                    const cardStatusTag = card.querySelector('.status-tag');
                    if (cardStatusTag) {
                        cardStatusTag.textContent = newStatus;
                        cardStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`; // Обновление класса
                    } else {
                        const newCardStatusTag = document.createElement('span');
                        newCardStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                        newCardStatusTag.textContent = newStatus;
                        card.querySelector('.movie-genres').insertAdjacentElement('afterend', newCardStatusTag);
                    }

                    // Отправка нового статуса на сервер
                    try {
                        const response = await fetch('/users/1/interactions', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({status: newStatus, movie_id: movieId})
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

    // Синхронизация скрытого поля лимита с селектором
    if (limitSelector && limitHiddenInput) {
        limitSelector.addEventListener('change', () => {
            limitHiddenInput.value = limitSelector.value; // Обновление скрытого поля
        });
        // Инициализация значения скрытого поля
        limitHiddenInput.value = limitSelector.value;
    }

    // Обработка изменения количества отображаемых карточек
    if (limitSelector) {
        limitSelector.addEventListener('change', () => {
            const queryParams = new URLSearchParams(window.location.search);
            queryParams.set('limit', limitSelector.value); // Обновление параметра limit в URL
            window.location.href = `${window.location.pathname}?${queryParams.toString()}`; // Перезагрузка страницы
        });
    }

    // Открытие/закрытие выпадающего меню "Library"
    dropdownLink.addEventListener('click', (e) => {
        e.preventDefault(); // Отмена стандартного поведения ссылки
        dropdownContent.classList.toggle('active'); // Переключение класса active (см. .dropdown-content.active в CSS)
    });

    // Закрытие выпадающего меню при клике вне его области
    document.addEventListener('click', (e) => {
        if (!dropdownLink.contains(e.target) && !dropdownContent.contains(e.target)) {
            dropdownContent.classList.remove('active'); // Удаление класса active
        }
    });

    // Закрытие модального окна
    modalClose.addEventListener('click', () => {
        modal.style.display = 'none'; // Скрытие модального окна (см. .modal display: none в CSS)
    });

    // Закрытие модального окна при клике вне его контента
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none'; // Скрытие модального окна
        }
    });

    // Первоначальное добавление обработчиков для карточек фильмов
    attachMovieCardHandlers();
});

// Переключение темы (светлая/тёмная)
const themeToggle = document.querySelector('.theme-toggle'); // Кнопка переключения темы (см. .theme-toggle в CSS)
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme'); // Переключение тёмной темы (см. body.dark-theme в CSS)
    document.body.classList.toggle('light-theme'); // Переключение светлой темы (см. body.light-theme в CSS)
    // Сохранение темы в localStorage
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
});