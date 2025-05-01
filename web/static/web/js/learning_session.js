const INACTIVITY_TIME = 30000;
const MIN_SESSION_TIME = 5000;

let sessionStartTime = null;
let lastActivityTime = null;
let isSessionActive = false;
let inactivityTimer = null;
let isSending = false;

const activityEvents = ['mousemove', 'scroll', 'click', 'keydown', 'touchstart'];

activityEvents.forEach(event => {
    window.addEventListener(event, handleActivity, { passive: true });
});


function handleActivity() {
    const now = new Date();
    lastActivityTime = now;

    if (!isSessionActive) {
        startNewSession();
    }

    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(endSession, INACTIVITY_TIME);
}

function startNewSession() {
    sessionStartTime = new Date();
    isSessionActive = true;
    console.log('Session started: ', sessionStartTime);
}

async function endSession() {
    if (!isSessionActive || isSending) return;

    const now = new Date();
    const sessionDuration = now - sessionStartTime;

    console.log('Session ended: ', now);
    console.log('Session duration: ', sessionDuration);

    if (sessionDuration < MIN_SESSION_TIME) {
        isSessionActive = false;
        sessionStartTime = null;
        return;
    }

    isSending = true;
    console.log(window.location.href);
    sendToServer({
        session_start: sessionStartTime.toISOString(),
        session_end: now.toISOString(),
        duration: Math.floor(sessionDuration / 1000),
        page_url: window.location.href
    }).finally(() => {
        resetSession();
        isSending = false;
    });
}

function resetSession() {
    isSessionActive = false;
    sessionStartTime = null;
    clearTimeout(inactivityTimer);
}

function sendToServer(data) {
    return new Promise((resolve) => {
        fetch('/api/track_session/',{
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data),
            keepalive: true
        }).then(resolve).catch(resolve);
    });
}

window.addEventListener('beforeunload', endSession);
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
        endSession();
    }
});