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