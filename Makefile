install:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
	poetry install

jupyter:
	poetry run jupyter lab

check:
	poetry run isort .
	poetry run black . 
	poetry run pylint pre_law_viewer/ tests/

test:
	poetry run pytest tests/


