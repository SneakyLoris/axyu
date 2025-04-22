const categoryName = document.getElementById('categoryName');
const questionElement = document.getElementById('question');
const optionsElement = document.getElementById('options');
const progressBar = document.getElementById('progressBar');
const correctCountElement = document.getElementById('correctCount');
const wrongCountElement = document.getElementById('wrongCount');
const remainingCountElement = document.getElementById('remainingCount');

let params = new URLSearchParams(document.location.search);
const category_id = parseInt(params.get('category_id'))
let currentTest = null;
let correctAnswers = 0;
let wrongAnswers = 0;
let totalQuestions = 0;
let currentQuestionIndex = 0;
let questions = [];
    
    // Загрузка теста
async function loadTest() {
    try {
        const response = await fetch(`/api/learning/get_test_questions?category_id=${category_id}`);
        const data = await response.json();

        if (data.questions && data.questions.length > 0) {
            questions = data.questions;
            totalQuestions = questions.length;
            currentQuestionIndex = 0;
            correctAnswers = 0;
            wrongAnswers = 0;
            setRemaining(totalQuestions);
            showNextQuestion();
        } else {
            questionElement.textContent = "Нет вопросов для теста в этой категории";
            optionsElement.innerHTML = '';
        }
    } catch (error) {
        console.error('Ошибка загрузки теста:', error);
        questionElement.textContent = "Ошибка загрузки теста";
    }
}

document.addEventListener('DOMContentLoaded', loadTest);

function showNextQuestion() {
    if (currentQuestionIndex >= totalQuestions) {
        finishTest();
        return;
    }

    currentTest = questions[currentQuestionIndex];
    questionElement.textContent = currentTest.word;

    optionsElement.innerHTML = ''
    optionsElement.style = "grid-template-columns: 1fr 1 fr";

    currentTest.options.forEach((option, index) => {
        console.log(option.translation);
        const optionElement = document.createElement('div');
        optionElement.className = 'option';
        optionElement.textContent = option.translation;
        optionElement.dataset.index = index;
        optionElement.addEventListener('click', checkAnswer);
        optionsElement.appendChild(optionElement);
    });

    progressBar.style.width = `${(currentQuestionIndex / totalQuestions) * 100}%`;
        remainingCountElement.textContent = totalQuestions - currentQuestionIndex;
}

function checkAnswer(e) {
    const selectedOption = e.target;
    const selectedIndex = parseInt(selectedOption.dataset.index);

    document.querySelectorAll('.option').forEach(option => {
        option.removeEventListener('click', checkAnswer);
        option.style.cursor = 'default';
    });

    is_right = currentTest.options[selectedIndex].is_correct;

    if (is_right) {
        selectedOption.classList.add('correct');
        incrementCorrect();
    } else {
        selectedOption.classList.add('wrong');
        incrementWrong();
    }

    const correctIndex = currentTest.options.findIndex(option => option.is_correct);
    document.querySelector(`.option[data-index="${correctIndex}"]`).classList.add('correct');

    UpdateStat(is_right);
    
    setTimeout(() => {
        showNextQuestion();
    }, 1000);
}

function incrementCorrect() {
    correctAnswers += 1
    correctCountElement.textContent = correctAnswers
}

function incrementWrong() {
    wrongAnswers += 1
    wrongCountElement.textContent = wrongAnswers
}

function setRemaining(remain) {
    remainingCountElement.textContent = remain
}

function UpdateStat(is_last_right) {
    if (is_last_right) {
        incrementCorrect();
    } else {
        incrementWrong();
    }

    currentQuestionIndex += 1;
    setRemaining(totalQuestions - currentQuestionIndex);
}

function finishTest() {
    questionElement.textContent = `Тест завершен! Результат: ${correctAnswers} из ${totalQuestions}`;
    optionsElement.innerHTML = '';
    progressBar.style.width = '100%';

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'restart-button-container';
    
    // Кнопка для повторного прохождения теста
    const restartButton = document.createElement('button');
    restartButton.className = 'restart-button';
    restartButton.textContent = 'Пройти тест снова';
    restartButton.addEventListener('click', loadTest);

    buttonContainer.appendChild(restartButton);
    optionsElement.appendChild(buttonContainer);
    optionsElement.style = "grid-template-columns: 1fr";
}