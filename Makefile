poetry:
	curl -sSL https://install.python-poetry.org | python3 -

install:
	poetry install
	poetry run python -m spacy download de_core_news_sm

jupyter:
	poetry run jupyter lab

check:
	poetry run isort --profile black .
	poetry run black . 
	poetry run pylint lawinprogress/

test:
	poetry run pytest --cov="lawinprogress/" tests/

app:
	poetry run uvicorn lawinprogress.app.html:app --reload

requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

style:
	cd ./mybulma/ && npm run css-build
	cp ./mybulma/css/mystyles.css ./lawinprogress/templates/css/bulma.css
