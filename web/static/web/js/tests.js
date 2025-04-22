document.addEventListener('DOMContentLoaded', function() {
    const categoryName = document.getElementById('categoryName');
    const questionElement = document.getElementById('question');
    const optionsElement = document.getElementById('options');
    const progressBar = document.getElementById('progressBar');
    const correctCountElement = document.getElementById('correctCount');
    const wrongCountElement = document.getElementById('wrongCount');
    const remainingCountElement = document.getElementById('remainingCount');
    
    const category_id = categoryName.dataset.id;
    let currentTest = null;
    let correctAnswers = 0;
    let wrongAnswers = 0;
    let totalQuestions = 0;
    let currentQuestionIndex = 0;
    let questions = [];
    
    // Загрузка теста
    async function loadTest() {
        try {
            const response = await fetch(`/api/get_test_questions/?category_id=`);
            const data = await response.json();
            
            if (data.questions && data.questions.length > 0) {
                questions = data.questions;
                totalQuestions = questions.length;
                currentQuestionIndex = 0;
                correctAnswers = 0;
                wrongAnswers = 0;
                
                updateStats();
                showQuestion();
            } else {
                questionElement.textContent = "Нет вопросов для теста в этой категории";
                optionsElement.innerHTML = '';
            }
        } catch (error) {
            console.error('Ошибка загрузки теста:', error);
            questionElement.textContent = "Ошибка загрузки теста";
        }
    }
    
    // Показать текущий вопрос
    function showQuestion() {
        if (currentQuestionIndex >= questions.length) {
            finishTest();
            return;
        }
        
        currentTest = questions[currentQuestionIndex];
        questionElement.textContent = currentTest.word;
        
        // Очищаем предыдущие варианты
        optionsElement.innerHTML = '';
        
        // Создаем варианты ответов
        currentTest.options.forEach((option, index) => {
            const optionElement = document.createElement('div');
            optionElement.className = 'option';
            optionElement.textContent = option.translation;
            optionElement.dataset.index = index;
            optionElement.addEventListener('click', checkAnswer);
            optionsElement.appendChild(optionElement);
        });
        
        // Обновляем прогресс
        progressBar.style.width = `${(currentQuestionIndex / totalQuestions) * 100}%`;
        remainingCountElement.textContent = totalQuestions - currentQuestionIndex;
    }
    
    // Проверка ответа
    function checkAnswer(e) {
        const selectedOption = e.target;
        const selectedIndex = parseInt(selectedOption.dataset.index);
        
        // Блокируем все варианты
        document.querySelectorAll('.option').forEach(opt => {
            opt.removeEventListener('click', checkAnswer);
            opt.style.cursor = 'default';
        });
        
        // Проверяем ответ
        if (currentTest.options[selectedIndex].is_correct) {
            selectedOption.classList.add('correct');
            correctAnswers++;
        } else {
            selectedOption.classList.add('wrong');
            wrongAnswers++;
            
            // Подсвечиваем правильный ответ
            const correctIndex = currentTest.options.findIndex(opt => opt.is_correct);
            document.querySelector(`.option[data-index="${correctIndex}"]`).classList.add('correct');
        }
        
        updateStats();
        
        // Переход к следующему вопросу через 1.5 секунды
        setTimeout(() => {
            currentQuestionIndex++;
            showQuestion();
        }, 1500);
    }
    
    // Обновление статистики
    function updateStats() {
        correctCountElement.textContent = correctAnswers;
        wrongCountElement.textContent = wrongAnswers;
    }
    
    // Завершение теста
    function finishTest() {
        questionElement.textContent = `Тест завершен! Результат: ${correctAnswers} из ${totalQuestions}`;
        optionsElement.innerHTML = '';
        progressBar.style.width = '100%';
        
        // Кнопка для повторного прохождения теста
        const restartButton = document.createElement('button');
        restartButton.className = 'btn btn-primary';
        restartButton.textContent = 'Пройти тест снова';
        restartButton.addEventListener('click', loadTest);
        optionsElement.appendChild(restartButton);
    }
    
    // Начальная загрузка теста
    loadTest();
});