install:
	@pip install poetry
	@poetry install
	@poetry self add 'poetry-plugin-export<=1.9.0'

update:
	@poetry update

imports:
	@poetry run isort -a "from __future__ import annotations" mlclient -s "__init__.py" -s "__main__.py"
	@poetry run isort .

lint:
	@poetry run ruff check .

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

release-patch:
	@poetry run python scripts/release.py prepare patch

release-minor:
	@poetry run python scripts/release.py prepare minor

release-major:
	@poetry run python scripts/release.py prepare major

# Explicit prerelease target, e.g. VERSION=1.0.0rc1.
release-pre:
	@test -n "$(VERSION)" || (echo "Set VERSION, e.g. VERSION=1.0.0rc1"; exit 1)
	@poetry run python scripts/release.py prepare "$(VERSION)" --prerelease

release-tag:
	@poetry run python scripts/release.py tag

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

.PHONY: release-patch release-minor release-major release-pre release-tag
