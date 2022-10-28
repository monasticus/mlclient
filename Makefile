init:
	pip install -r requirements.txt

imports:
	isort .

test:
	pytest test/
