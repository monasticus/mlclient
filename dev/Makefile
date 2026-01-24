SHELL := /bin/sh

.PHONY: build up stop clean bash init deps ports

build:
	@docker compose build

up:
	@docker compose up -d

stop:
	@docker compose stop

clean:
	@docker compose down -v --remove-orphans

bash:
	@docker compose exec -it dev bash || docker compose exec -it dev sh

init: up deps ports

deps:
	@echo "[deps] Installing Python dependencies via Poetry in dev container..."
	@docker compose exec -it dev sh -c "cd /mlclient && poetry install"
	@echo "[deps] Done."

ports:
	@echo ""
	@echo "MarkLogic ports (host -> node)"
	@echo ""
	@echo "  single node : 8000-8010 , 7997"
	@echo "  cluster n1  : 7100-7110 , 7197"
	@echo "  cluster n2  : 7200-7210 , 7297"
	@echo "  cluster n3  : 7300-7310 , 7397"
	@echo ""
