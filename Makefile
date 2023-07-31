init:
	@python -m pip install pip-tools
	@pip-compile --extra dev pyproject.toml
	@pip install -r requirements.txt
	@pip install -e .

imports:
	@isort .
	@isort -a "from __future__ import annotations" mlclient

lint:
	@ruff .

lint-fix:
	@ruff . --fix

test:
	@pytest --cov=mlclient tests/

ml-start:
	@sudo /etc/init.d/MarkLogic start

ml-stop:
	@sudo /etc/init.d/MarkLogic stop

linters:
	@pip install --upgrade ruff
	@./meta/linters/look_for_new_linters.py

update-linters:
	@ruff linter --format=json > ./meta/linters/linters.json
