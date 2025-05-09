document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const userAvatar = document.getElementById('userAvatar');

    if (userAvatar) {
        userAvatar.addEventListener('click', function() {
            if (searchResults) {
                searchResults.style.display = 'none';
            }
        });
    }

    searchInput.addEventListener('input', async function(e) {
        const query = e.target.value.trim().toLowerCase();

    if (query.length < 2) {
        searchResults.innerHTML = '';
        searchResults.style.display = 'none';
        return;
    }

        try {
            const response = await fetch(`/search_words/?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                searchResults.innerHTML = '';
                data.results.forEach(item => {
                    const isExactMatch = item.word.toLowerCase() === query || item.translation.toLowerCase() === query;
                    const resultItem = document.createElement('div');
                    resultItem.className = 'search-result-item';
                    resultItem.innerHTML = `
                        <a href="/categories/${encodeURIComponent(item.category_id)}?highlight=${encodeURIComponent(item.word)}&exact=true"
                           data-exact="${isExactMatch}"
                           data-word="${item.word.toLowerCase()}">
                           ${item.word} /${item.transcription}/ ${item.translation} - ${item.category_name}
                        </a>
                    `;
                    searchResults.appendChild(resultItem);
                });
                searchResults.style.display = 'block';
            } else {
                searchResults.innerHTML = '<div class="no-results">Ничего не найдено</div>';
                searchResults.style.display = 'block';
            }
        } catch (error) {
            console.error('Ошибка поиска:', error);
            searchResults.innerHTML = '<div class="error">Ошибка при поиске</div>';
            searchResults.style.display = 'block';
        }
    });

    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
});