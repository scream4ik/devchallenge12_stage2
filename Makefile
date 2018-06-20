.PHONY: up test

up:
	-@docker-compose up --build

test:
	-@docker-compose exec app pytest -s
