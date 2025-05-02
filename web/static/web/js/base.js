document.addEventListener('DOMContentLoaded', function() {
    const dropdown = document.getElementById('userDropdown');
    const avatar = document.getElementById('userAvatar');
    const dropdownContent = document.getElementById('dropdownContent');
    let closeTimer;

    function closeDropdown() {
        dropdownContent.classList.remove('show');
    }

    function toggleDropdown(e) {
        e.stopPropagation();
        dropdownContent.classList.toggle('show');
    }

    avatar.addEventListener('click', toggleDropdown);
    
    dropdown.addEventListener('mouseleave', function() {
        closeTimer = setTimeout(closeDropdown, 200);
    });
    
    dropdownContent.addEventListener('mouseenter', function() {
        clearTimeout(closeTimer);
    });
    
    dropdownContent.addEventListener('mouseleave', closeDropdown);
});