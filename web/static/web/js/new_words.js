const word = document.getElementById("word");
const translation = document.getElementById("translation");
const wordsTotal = document.getElementById("wordsTotal");
const wordsLearned = document.getElementById("wordsLearned");
const wordsRemain = document.getElementById("wordsRemain");
const btnKnow = document.getElementById("btnKnow");
const btnDontKnow = document.getElementById("btnDontKnow");


async function loadNewCard() {
    alert('load new card')
}

async function sendResult(isKnown) {
    alert(`send result: ${isKnown}`)
}


btnKnow.addEventListener('click', function() {
    sendResult(true);
});

btnDontKnow.addEventListener('click', function() {
    sendResult(false);
});