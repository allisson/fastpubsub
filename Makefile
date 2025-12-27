.PHONY: test
test:
	uv run pytest -v

.PHONY: lint
lint:
	uv run pre-commit run --all-files

.PHONY: start-postgresql
start-postgresql:
	docker run --name postgres-fastpubsub \
		--restart unless-stopped \
		-e POSTGRES_USER=fastpubsub \
		-e POSTGRES_PASSWORD=fastpubsub \
		-e POSTGRES_DB=fastpubsub \
		-p 5432:5432 \
		-d postgres:14-alpine

.PHONY: remove-postgresql
remove-postgresql:
	docker kill $$(docker ps -aqf name=postgres-fastpubsub)
	docker container rm $$(docker ps -aqf name=postgres-fastpubsub)

.PHONY: create-migration
create-migration:
	uv run alembic revision -m "New migration"

.PHONY: run-db-migrate
run-db-migrate:
	PYTHONPATH=./ uv run python fastpubsub/main.py

.PHONY: docker-build
docker-build:
	docker build --rm -t fastpubsub .
