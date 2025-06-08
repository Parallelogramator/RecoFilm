document.addEventListener('DOMContentLoaded', () => {
    const dropdownLink = document.getElementById('library-link');
    const dropdownContent = document.querySelector('.dropdown-content');
    const modal = document.getElementById('movieModal');
    const modalBody = modal.querySelector('.modal-body');
    const modalClose = modal.querySelector('.modal-close');

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

    // Обработчик для карточек фильмов
    document.querySelectorAll('.movie-card').forEach(card => {
        card.addEventListener('click', (e) => {
            // Извлечение данных из карточки
            const movieId = card.dataset.movieId;
            const title = card.querySelector('.movie-title').textContent;
            const year = card.querySelector('.movie-year').textContent;
            const rating = card.querySelector('.movie-rating').textContent;
            const genres = Array.from(card.querySelectorAll('.genre-tag')).map(genre => genre.textContent);
            const statusTag = card.querySelector('.status-tag');
            const currentStatus = statusTag ? statusTag.textContent : '';
            const description = card.querySelector('.movie-description')?.textContent || 'Описание отсутствует';

            // Формирование содержимого модального окна
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
                        <option value="Просмотрено" ${currentStatus === 'Просмотрено' ? 'selected' : ''}>Просмотрено</option>
                        <option value="Понравилось" ${currentStatus === 'Понравилось' ? 'selected' : ''}>Понравилось</option>
                        <option value="Хочу посмотреть" ${currentStatus === 'Хочу посмотреть' ? 'selected' : ''}>Хочу посмотреть</option>
                        <option value="Брошено" ${currentStatus === 'Брошено' ? 'selected' : ''}>Брошено</option>
                        <option value="Смотрю" ${currentStatus === 'Смотрю' ? 'selected' : ''}>Смотрю</option>
                    </select>
                </div>
                <div class="movie-description">${description}</div>
            `;

            // Показать модальное окно
            modal.style.display = 'flex';

            // Обработчик выбора статуса в модальном окне
            const statusSelector = modalBody.querySelector('.status-selector select');
            statusSelector.addEventListener('change', async (e) => {
                const newStatus = e.target.value;
                const modalStatusTag = modalBody.querySelector('.status-tag');

                // Обновляем статус в модальном окне
                if (modalStatusTag) {
                    modalStatusTag.textContent = newStatus;
                    modalStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                } else {
                    const newStatusTag = document.createElement('span');
                    newStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                    newStatusTag.textContent = newStatus;
                    modalBody.querySelector('.movie-genres').insertAdjacentElement('afterend', newStatusTag);
                }

                // Обновляем статус на карточке
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

                // Отправка POST-запроса на сервер
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
});

const themeToggle = document.querySelector('.theme-toggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');
    // Сохранить выбор темы в localStorage
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
});

// Загрузить сохранённую тему
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.body.classList.add(savedTheme === 'dark' ? 'dark-theme' : 'light-theme');
}