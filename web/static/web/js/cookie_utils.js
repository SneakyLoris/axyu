function getCookie(name) {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith(`${name}=`));
    
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
}