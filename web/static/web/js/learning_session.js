const INACTIVITY_TIME = 30000;

let sessionStartTime = null;
let lastActivityTime = null;
let isSessionActive = false;
let inactivityTimer = null;
let isSending = false;

const activityEvents = ['mousemove', 'scroll', 'click', 'keydown', 'touchstart'];

window.session_id = null;

activityEvents.forEach(event => {
    window.addEventListener(event, handleActivity, { passive: true });
});


async function handleActivity() {
    const now = new Date();
    lastActivityTime = now;

    if (!isSessionActive) {
        await startNewSession();
    }

    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(endSession, INACTIVITY_TIME);
}

async function startNewSession() {
    sessionStartTime = new Date();
    isSessionActive = true;

    const response = await sendToServer({
        type: 'session_start',
        session_start: sessionStartTime.toISOString(),
        page_url: window.location.href,
    });

    const data = await response.json()
    window.session_id = data['session_id'];
}

async function endSession() {
    if (!isSessionActive || isSending) return;

    const now = new Date();
    const sessionDuration = now - sessionStartTime;

    isSending = true;
    
    sendToServer({
        type: 'session_end',
        session_id: window.session_id,
        session_end: now.toISOString(),
        duration: Math.floor(sessionDuration / 1000),
    }).finally(() => {
        resetSession();
        isSending = false;
    });
}

function resetSession() {
    isSessionActive = false;
    sessionStartTime = null;
    window.session_id = null;
    clearTimeout(inactivityTimer);
}

function sendToServer(data) {
    return new Promise((resolve) => {
        fetch('/track_session/',{
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