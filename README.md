<h1 align="center">Здарова там!</h1>
<h4 align="justify">Мы небольшая команда Казанского федерального и 
пишем проект для Цифровых кафедр.</h4>
<h4>Пока тут ничего нет, но это ненадолго</h4><hr>

 ### Команды для запуска проекта:

- `python -m venv venv` - создание виртуального окружения;
- `source venv/bin/activate` - вход в виртуальное окружение;
- `pip install -r requirements.txt` - установка зависимостей;
- `python manage.py migrate` - миграция моделей;
- `python manage.py runserver` - запуск сервера для разработки.

### Команды для запуска контейнера:

- `docker build -t ck_postgres .`
- `docker run --name ck_postges_container -p 5432:5432 -d ck_postgres`