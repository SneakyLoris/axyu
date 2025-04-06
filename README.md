<h1 align="center">Здарова там!</h1>
<h4 align="justify">Мы небольшая команда Казанского федерального и 
пишем проект для Цифровых кафедр.</h4>
<h4>Пока тут ничего нет, но это ненадолго</h4><hr>

<h3>Команды для запуска проекта:</h3>
<ul>
<li>'python3 -m venv venv' - создание виртуального окружения;</li>
<li>'source venv/bin/activate' - вход в виртуальное окружение;</li>
<li>'pip install -r requirements.txt' - установка зависимостей;</li>
<li>'python3 manage.py migrate' - миграция моделей;</li>
<li>'python3 manage.py runserver' - запуск сервера для разработки.</li>
</ul>

docker build -t ck_postgres .
docker run --name ck_postges_container -p 5432:5432 -d ck_postgres