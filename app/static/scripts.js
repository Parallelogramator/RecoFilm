document.addEventListener('DOMContentLoaded', () => {
    const dropdownLink = document.getElementById('library-link');
    const dropdownContent = document.querySelector('.dropdown-content');

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

    // Обработчик для карточек фильмов
    document.querySelectorAll('.movie-card').forEach(card => {
        card.addEventListener('click', (e) => {
            // Проверяем, не кликнули ли по статусному селектору
            if (e.target.closest('.status-selector')) {
                return; // Игнорируем клик по селектору статуса
            }

            const isExpanded = card.classList.contains('expanded');
            document.querySelectorAll('.movie-card').forEach(c => c.classList.remove('expanded'));
            if (!isExpanded) {
                card.classList.add('expanded');
                // Показать селектор статуса
                const statusSelector = card.querySelector('.status-selector');
                if (statusSelector) {
                    statusSelector.style.display = 'block';
                }
            } else {
                // Скрыть селектор статуса при повторном клике
                const statusSelector = card.querySelector('.status-selector');
                if (statusSelector) {
                    statusSelector.style.display = 'none';
                }
            }
        });

        // Обработчик выбора статуса
        const statusSelector = card.querySelector('.status-selector select');
        if (statusSelector) {
            statusSelector.addEventListener('change', async (e) => {
                const movieId = card.dataset.movieId; // Предполагаем, что movieId хранится в data-атрибуте
                const newStatus = e.target.value;
                const statusTag = card.querySelector('.status-tag');

                // Обновляем отображаемый статус
                if (statusTag) {
                    statusTag.textContent = newStatus;
                    statusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                } else {
                    // Создаём новый тег статуса, если его нет
                    const newStatusTag = document.createElement('span');
                    newStatusTag.className = `status-tag status-${newStatus.toLowerCase().replace(/\s+/g, '-')}`;
                    newStatusTag.textContent = newStatus;
                    card.querySelector('.movie-genres').insertAdjacentElement('afterend', newStatusTag);
                }

                // Отправка запроса на сервер (заглушка, нужно реализовать API)
                try {
                    const response = await fetch(`/api/interactions/${movieId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: newStatus })
                    });
                    if (!response.ok) {
                        console.error('Ошибка при обновлении статуса');
                    }
                } catch (error) {
                    console.error('Ошибка сети:', error);
                }
            });
        }
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
const savedemore = localStorage.getItem('theme');
if (savedTheme) {
    document.body.classList.add(savedTheme === 'dark' ? 'dark-theme' : 'light-theme');
}