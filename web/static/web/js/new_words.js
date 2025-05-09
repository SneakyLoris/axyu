const flashcard = document.getElementById("flashcard");
const controls = document.getElementById("controls");
const word = document.getElementById("word");
const translation = document.getElementById("translation");
const transcription = document.getElementById("transcription");
const btnKnow = document.getElementById("btnKnow");
const btnDontKnow = document.getElementById("btnDontKnow");
const noWordMessage = document.getElementById('noWordsMessage');

const csrftoken = getCookie('csrftoken');
let currentWordId = null;

async function loadNewCard() {
    try {
        const response = await fetch('/learning/get_new_word/');
        const data = await response.json();

        if (data['status'] == 'success') {
            currentWordId = data['id'];
            word.textContent = data['word'];
            translation.textContent = data['translation'];
            transcription.textContent = `[${data['transcription']}]`;
        } else {
            flashcard.style.display = 'none';
            controls.style.display = 'none';
            noWordMessage.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка загрузки карточки:', error);       
    }
}

loadNewCard();

async function sendResult(isKnown) {
    const response = await fetch('/learning/new_word_send_result/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'include',
        body: JSON.stringify({
          word_id: currentWordId,
          is_known: isKnown
        })
    });

    if (!response.ok) {
        console.error(`Error: ${response.text}`);
    }

    const result = await response.json();
    await loadNewCard();
}


btnKnow.addEventListener('click', function() {
    sendResult(true);
});

btnDontKnow.addEventListener('click', function() {
    sendResult(false);
});