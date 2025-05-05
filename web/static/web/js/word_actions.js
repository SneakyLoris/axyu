let currentWordId = null;

function showWordContextMenu(event, wordId) {
    event.preventDefault();
    currentWordId = wordId;
    
    const menu = document.getElementById('wordContextMenu');
    menu.style.display = 'block';
    menu.style.left = `${event.pageX}px`;
    menu.style.top = `${event.pageY}px`;
    
    return false;
}


document.addEventListener('click', function() {
    const menu = document.getElementById('wordContextMenu');
    if (menu) menu.style.display = 'none';
});


document.querySelectorAll('.context-menu-item').forEach(item => {
    item.addEventListener('click', function() {
        const action = this.getAttribute('data-action');
        if (!currentWordId) return;
        
        switch(action) {
            case 'edit':
                console.log('Редактировать слово:', currentWordId);
                break;
            case 'delete':
                console.log('Удалить слово:', currentWordId);
                break;
            case 'change-status':
                console.log('Изменить статус слова:', currentWordId);
                break;
        }
    });
});


document.querySelectorAll('.word-row').forEach(row => {
    row.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        currentWordId = this.dataset.wordId;
        const menu = document.getElementById('wordContextMenu');
        menu.style.display = 'block';
        menu.style.left = `${e.pageX}px`;
        menu.style.top = `${e.pageY}px`;
    });
});

function showWordContextMenu(event, wordId, wordStatus) {
    event.preventDefault();
    currentWordId = wordId;
    
    const menu = document.getElementById('wordContextMenu');
    menu.innerHTML = ''; // Очищаем меню
    
    // Генерируем меню в зависимости от статуса
    switch(wordStatus) {
        case 'new':
            addMenuItem(menu, 'plus', 'Начать учить', 'start-learning');
            addMenuItem(menu, 'check', 'Отметить как известное', 'mark-known');
            break;
            
        case 'in_progress':
            addMenuItem(menu, 'sync-alt', 'Сбросить прогресс', 'reset-progress');
            addMenuItem(menu, 'plus', 'Добавить к изучаемым', 'add-to-learning');
            break;
            
        case 'learned':
            addMenuItem(menu, 'sync-alt', 'Сбросить прогресс', 'reset-progress');
            break;
    }
    
    // Общие пункты для всех статусов
    addDivider(menu);
    addMenuItem(menu, 'pencil-alt', 'Редактировать', 'edit');
    addDivider(menu);
    addMenuItem(menu, 'trash-alt', 'Удалить', 'delete', true);
    
    // Позиционирование
    positionMenu(event, menu);
}

// Вспомогательные функции
function addMenuItem(menu, icon, text, action, isDanger = false) {
    const item = document.createElement('a');
    item.href = '#';
    item.className = `context-menu-item ${isDanger ? 'context-menu-item--danger' : ''}`;
    item.dataset.action = action;
    item.innerHTML = `<span class="fas fa-${icon}"></span> ${text}`;
    item.addEventListener('click', function(e) {
        e.preventDefault();
        handleMenuAction(action);
    });
    menu.appendChild(item);
}

function addDivider(menu) {
    const divider = document.createElement('div');
    divider.className = 'context-menu-divider';
    menu.appendChild(divider);
}