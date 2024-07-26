init:
	docker compose up -d
	docker compose exec -it dev sh -c "cd /mlclient && poetry install"

build:
	docker compose build

up:
	docker compose up -d

stop:
	docker compose stop

clean:
	docker compose down -v

bash:
	docker compose exec dev bash
