let currentWordId = null;
let currentCategoryId = null;
let currentWordText = '';
let currentTranslation = '';
let currentTranscription = '';

// Функция для отображения контекстного меню
function showWordContextMenu(event, rowElement) {
    event.preventDefault();
    
    // Сохраняем данные слова
    currentWordId = rowElement.dataset.wordId;
    currentCategoryId = rowElement.dataset.categoryId;
    const wordParts = rowElement.querySelector('.english-word').textContent.split('/');
    currentWordText = wordParts[0].trim();
    currentTranslation = rowElement.querySelector('.russian-word').textContent;
    currentTranscription = wordParts[1] || '';
    
    // Получаем статус и права доступа
    const wordStatus = rowElement.dataset.status;
    const isOwner = rowElement.dataset.isOwner === 'true';
    
    // Создаем меню
    const menu = document.getElementById('wordContextMenu');
    menu.innerHTML = '';
    
    // Добавляем пункты меню
    addMenuItems(menu, wordStatus, isOwner);
    
    // Позиционируем меню
    positionMenu(event, menu);
}

// Добавление пунктов меню
function addMenuItems(menu, status, isOwner) {
    switch(status) {
        case 'new':
            addMenuItem(menu, 'plus', 'Начать учить', 'start-learning');
            addMenuItem(menu, 'check', 'Отметить как известное', 'mark-known');
            break;
            
        case 'in_progress':
            addMenuItem(menu, 'check', 'Отметить как известное', 'mark-known');
            addMenuItem(menu, 'sync-alt', 'Сбросить прогресс', 'reset-progress');
            break;
            
        case 'learned':
            addMenuItem(menu, 'sync-alt', 'Сбросить прогресс', 'reset-progress');
            break;
    }
    
    if (isOwner) {
        addDivider(menu);
        addMenuItem(menu, 'pencil-alt', 'Редактировать', 'edit');
        addDivider(menu);
        addMenuItem(menu, 'trash-alt', 'Удалить', 'delete', true);
    }
}

// Создание пункта меню
function addMenuItem(menu, icon, text, action, isDanger = false) {
    const item = document.createElement('a');
    item.href = '#';
    item.className = `context-menu-item ${isDanger ? 'context-menu-item--danger' : ''}`;
    item.dataset.action = action;
    item.innerHTML = `<span class="fas fa-${icon}"></span> ${text}`;
    item.addEventListener('click', (e) => handleMenuClick(e, action));
    menu.appendChild(item);
}

// Добавление разделителя
function addDivider(menu) {
    const divider = document.createElement('div');
    divider.className = 'context-menu-divider';
    menu.appendChild(divider);
}

// Позиционирование меню
function positionMenu(event, menu) {
    const scrollY = window.scrollY;
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    const maxX = viewportWidth - menu.offsetWidth - 10;
    const maxY = scrollY + viewportHeight - menu.offsetHeight - 10;

    const x = Math.min(event.pageX, maxX);
    const y = Math.min(event.pageY, maxY);

    menu.style.display = 'block';
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
}

// Закрытие меню
function closeContextMenu() {
    const menu = document.getElementById('wordContextMenu');
    if (menu) menu.style.display = 'none';
}

// Обработка клика по пункту меню
async function handleMenuClick(e, action) {
    e.preventDefault();
    if (!currentWordId || !currentCategoryId) return;

    const actions = {
        'start-learning': { url: `/words/start_learning/${currentWordId}/` },
        'mark-known': { url: `/words/mark_known/${currentWordId}/` },
        'reset-progress': { url: `/words/reset_progress/${currentWordId}/` },
        'edit': { url: `/words/edit/${currentCategoryId}/${currentWordId}/` },
        'delete': { 
            url: `/words/delete/${currentWordId}/`,
            Confirm: true
        }
    };

    if (action === 'edit') {
        window.location.href = `/words/edit/${currentCategoryId}/${currentWordId}/`;
        return;
    }

    const config = actions[action];

    if (!config) return;

    try {
        if (config.Confirm && !confirm('Вы уверены, что хотите удалить это слово?')) {
            return;
        }

        let response = await callDjangoView(config.url);
        const currentUrl = window.location.href;
        const baseUrl = currentUrl.split('?')[0];

        sessionStorage.setItem('savedScrollPosition', window.scrollY);
        window.location.href = baseUrl;
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при выполнении операции');
    } finally {
        closeContextMenu();
    }
}

// Отправка запроса на сервер
async function callDjangoView(url, data = null) {
    const csrftoken = getCookie('csrftoken');
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.word-row').forEach(row => {
        row.addEventListener('contextmenu', function(e) {
            showWordContextMenu(e, this);
        });
    });
    
    // Закрытие меню при клике вне его
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.context-menu') && !e.target.closest('.word-row')) {
            closeContextMenu();
        }
    });
});


window.addEventListener('load', () => {
    const savedPosition = sessionStorage.getItem('savedScrollPosition');
    if (savedPosition) {
        window.scrollTo(0, parseInt(savedPosition));
        sessionStorage.removeItem('savedScrollPosition'); // Очищаем сохранённое значение
    }
});