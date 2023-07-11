init:
	@python -m pip install pip-tools
	@pip-compile --extra dev pyproject.toml
	@pip install -r requirements.txt
	@pip install -e .

imports:
	@isort .

test:
	@pytest --cov=mlclient tests/

ml-start:
	@sudo /etc/init.d/MarkLogic start

ml-stop:
	@sudo /etc/init.d/MarkLogic stop
