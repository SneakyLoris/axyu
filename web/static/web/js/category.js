const csrftoken = getCookie('csrftoken');


document.querySelectorAll('.category-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const categoryId = this.dataset.id;
        const isChecked = this.checked;
    
        const response = await fetch('/api/update_user_categories/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            credentials: 'include',
            body: JSON.stringify({
              category_id: categoryId,
              is_checked: isChecked
            })
        });

        if (!response.ok) {
            this.checked = !isChecked;
        }

        const result = await response.json();
    });
});