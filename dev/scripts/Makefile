linters:
	poetry update ruff
	@poetry run ./look-for-new-linters/look_for_new_linters.py

update-linters:
	@poetry run ruff linter --output-format=json > ./look-for-new-linters/linters.json

mimetypes:
	@poetry run python ./get-mimetypes/get-mimetypes.py

populate:
	@poetry run python populate-database/populate-database.py