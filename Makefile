PYTHON=python
COMMAND_LOAD_WORDS=load_words
MANAGE=manage.py
DOCKER_DB_TAG=ck_postgres
DOCKER_DB_CONTAINER_NAME=$(DOCKER_DB_TAG)_container
DOCKER_DB_CONTAINER_PORT=5432
DOCKER_DB_LOCAL_PORT=5432
WORDLISTS_TRANSLATED_DIR=wordlists/translated


makemigrations:
	$(PYTHON) $(MANAGE) makemigrations

migrate:
	$(PYTHON) $(MANAGE) migrate

build_docker_db_image:
	docker build -t $(DOCKER_DB_TAG) .

run_docker_db:
	docker run --name $(DOCKER_DB_CONTAINER_NAME) -p $(DOCKER_DB_LOCAL_PORT):$(DOCKER_DB_CONTAINER_PORT) -d $(DOCKER_DB_TAG)

load_words:
	$(PYTHON) $(MANAGE) $(COMMAND_LOAD_WORDS) $(WORDLISTS_TRANSLATED_DIR)
