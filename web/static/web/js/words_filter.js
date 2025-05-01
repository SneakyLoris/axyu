const filterSelect = document.getElementById('wordFilter');
const wordsList = document.getElementById('wordsList');
const wordRows = Array.from(document.querySelectorAll('.word-row'));

filterSelect.addEventListener('change', on_change);

function on_change() {
    const filterValue = this.value;
    
    wordRows.forEach(row => {
        row.style.display = 'flex';
        
        switch(filterValue) {
            case 'status_learned':
                if (!row.classList.contains('status-learned')) row.style.display = 'none';
                break;
            case 'status_in_progress':
                if (!row.classList.contains('status-in_progress')) row.style.display = 'none';
                break;
            case 'status_new':
                if (!row.classList.contains('status-new')) row.style.display = 'none';
                break;
            case 'default':
                break;
        }
    });
}