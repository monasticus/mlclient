install:
	@pip install poetry
	@poetry install
	@poetry self add 'poetry-bumpversion<0.3.1'

update:
	@poetry update

imports:
	@poetry run isort -a "from __future__ import annotations" mlclient -s "__init__.py" -s "__main__.py"
	@poetry run isort .

lint:
	-@poetry run ruff .

lintp:
	-@poetry run ruff . --preview

lint-fix:
	-@poetry run ruff . --fix

lintp-fix:
	-@poetry run ruff . --preview --fix

format: imports lint-fix
	@poetry run ruff format .

unit-test:
	@poetry run pytest --cov=mlclient tests/unit

integration-test:
	@poetry run pytest --cov=mlclient/clients tests/integration

test: unit-test integration-test

ml-start:
	@sudo /etc/init.d/MarkLogic start

ml-stop:
	@sudo /etc/init.d/MarkLogic stop

linters:
	poetry update ruff
	@./meta/linters/look_for_new_linters.py

publish:
	@poetry --build publish

update-linters:
	@poetry run ruff linter --output-format=json > ./meta/linters/linters.json

mimetypes:
	@./scripts/get-mimetypes/get-mimetypes.py

branches:
	@git branch | grep -E -v "(main)|(bump.*)" | xargs git branch -D
