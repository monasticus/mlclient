install:
	@pip install poetry
	@poetry install
	@poetry self add 'poetry-bumpversion>=0.3.3'
	@poetry self add 'poetry-plugin-export<=1.9.0'

update:
	@poetry update

imports:
	@poetry run isort -a "from __future__ import annotations" mlclient -s "__init__.py" -s "__main__.py"
	@poetry run isort .

lint:
	-@poetry run ruff check .

lintp:
	-@poetry run ruff check . --preview

lint-fix:
	-@poetry run ruff check . --fix

lintp-fix:
	-@poetry run ruff check . --preview --fix

format: imports
	@poetry run ruff format . > /dev/null 2>&1
	@poetry run ruff format .
	@poetry run ruff check . --fix


unit-test:
	@poetry run pytest --cov=mlclient tests/unit

integration-test:
	@poetry run pytest --cov=mlclient/clients tests/integration

test: unit-test integration-test

publish:
	@poetry --build publish

branches:
	@git branch | grep -E -v "(main)|(bump.*)" | xargs git branch -D

.PHONY: docs-install docs-serve docs-build docs-deploy-dev

docs-install:
	@poetry install --only main,docs

docs-serve:
	@poetry run mkdocs serve

docs-build:
	@poetry run mkdocs build --strict
	@poetry run python scripts/check_docs.py

# Publishing remains a CI-only operation. Requires authenticated GitHub CLI.
docs-deploy-dev:
	@gh workflow run docs.yml --ref main
