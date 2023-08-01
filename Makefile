install:
	@pip install poetry
	@poetry install
	@poetry self add poetry-bumpversion

update:
	@poetry update

imports:
	@poetry run isort .
	@poetry run isort -a "from __future__ import annotations" mlclient

lint:
	@poetry run ruff .

lint-fix:
	@poetry run ruff . --fix

test:
	@poetry run pytest --cov=mlclient tests/

ml-start:
	@sudo /etc/init.d/MarkLogic start

ml-stop:
	@sudo /etc/init.d/MarkLogic stop

linters:
	poetry update ruff
	@./meta/linters/look_for_new_linters.py

update_linters:
	@poetry run ruff linter --format=json > ./meta/linters/linters.json
