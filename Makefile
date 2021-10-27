poetry:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

install:
	poetry install
	poetry run python -m spacy download de_core_news_sm

jupyter:
	poetry run jupyter lab

check:
	poetry run isort .
	poetry run black . 
	poetry run pylint lawinprogress/ tests/

test:
	poetry run pytest --cov="lawinprogress/" tests/

