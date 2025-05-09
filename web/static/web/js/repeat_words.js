const flashcard = document.getElementById("flashcard");
const controls = document.getElementById("memoryControls");
const word = document.getElementById("word");
const translation = document.getElementById("translation");
const transcription = document.getElementById("transcription");
const btnKnow = document.getElementById("btnKnow");
const btnDontKnow = document.getElementById("btnDontKnow");
const noWordMessage = document.getElementById('noWordsMessage');
const btnShowTranslation = document.getElementById('btnShowTranslation');

const csrftoken = getCookie('csrftoken');
let currentWordId = null;

async function loadWordForRepeat() {
    try {
        const response = await fetch('/learning/get_word_repeat/');
        const data = await response.json();

        if (data['status'] == 'success') {
            currentWordId = data['id'];
            word.textContent = data['word'];
            translation.textContent = data['translation'];
            transcription.textContent = `[${data['transcription']}]`;
        } else {
            flashcard.style.display = 'none';
            controls.style.display = 'none';
            btnShowTranslation.style.display = 'none';
            noWordMessage.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка загрузки карточки:', error);       
    }    
}

loadWordForRepeat();

async function sendRepeatResult(remembered) {
    const response = await fetch('/learning/send_repeat_result/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'include',
        body: JSON.stringify({
          word_id: currentWordId,
          is_known: remembered, 
          session_id: window.session_id
        })
    });
}

btnKnow.addEventListener('click', function() {
    sendRepeatResult(true);
    translation.style.display = 'none';
    transcription.style.display = 'none';
    loadWordForRepeat();

});

btnDontKnow.addEventListener('click', function() {
    sendRepeatResult(false);
    translation.style.display = 'none';
    transcription.style.display = 'none';
    loadWordForRepeat();
});

btnShowTranslation.addEventListener('click', function() {
    translation.style.display = 'block';
    transcription.style.display = 'block';
});