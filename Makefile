run:
	poetry run uvicorn schema:app --reload

fmt:
	ruff check -s --fix --exit-zero .

lint list_strict:
	mypy .
	ruff check .

lint_fix: fmt lint

migrate:
	poetry run python -m yoyo apply -vvv --batch --database "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/books" ./migrations
