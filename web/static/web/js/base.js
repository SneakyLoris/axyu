document.addEventListener('DOMContentLoaded', function() {
    const dropdown = document.getElementById('userDropdown');
    const avatar = document.getElementById('userAvatar');
    const dropdownContent = document.getElementById('dropdownContent');
    

    avatar.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdownContent.classList.toggle('show');
    });
    
    document.addEventListener('click', function(e) {
        if (!dropdown.contains(e.target)) {
            dropdownContent.classList.remove('show');
        }
    });
    
    dropdown.addEventListener('mouseleave', function() {
        setTimeout(() => {
            if (!dropdown.matches(':hover')) {
                dropdownContent.classList.remove('show');
            }
        }, 200);
    });
    
    dropdownContent.addEventListener('mouseenter', function() {
        clearTimeout(closeTimer);
    });
    
    dropdownContent.addEventListener('mouseleave', function() {
        dropdownContent.classList.remove('show');
    });
});