init:
	pip install -r requirements.txt

imports:
	isort .

test:
	pytest test/

ml-start:
	sudo /etc/init.d/MarkLogic start

ml-stop:
	sudo /etc/init.d/MarkLogic stop
