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

document.querySelectorAll('.movie-card').forEach(card => {
    card.addEventListener('click', () => {
        const isExpanded = card.classList.contains('expanded');
        document.querySelectorAll('.movie-card').forEach(c => c.classList.remove('expanded'));
        if (!isExpanded) {
            card.classList.add('expanded');
        }
    });
});