document.addEventListener('DOMContentLoaded', function() {
    const filterSelect = document.getElementById('wordFilter');
    if (filterSelect) {
        filterSelect.addEventListener('change', onFilterChange);
    }

    highlightWord();
});


function onFilterChange() {
    const filterValue = this.value;
    const wordRows = Array.from(document.querySelectorAll('.word-row'));

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

function highlightWord() {
    const params = new URLSearchParams(window.location.search);
    const highlightWord = params.get('highlight');
    const exactMatch = params.get('exact') === 'true';

    if (!highlightWord) return;

    const searchTerm = highlightWord.toLowerCase();
    const wordRows = document.querySelectorAll('.word-row');
    let firstMatch = null;

    for (const row of wordRows) {
        const wordElement = row.querySelector('.english-word');
        if (wordElement) {
            const wordText = wordElement.textContent.split('/')[0].trim().toLowerCase();

            // Для точного совпадения сравниваем полное слово. Для неточного - ищем подстроку
            const isMatch = exactMatch
                ? wordText === searchTerm
                : wordText.includes(searchTerm);

            if (isMatch) {
                firstMatch = row;
                if (exactMatch) break;
            }
        }
    }

    if (firstMatch) {
        firstMatch.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        setTimeout(() => {
            firstMatch.classList.add('highlighted');
            setTimeout(() => {
                firstMatch.classList.remove('highlighted');
            }, 1000);
        }, 1000);
    }
}