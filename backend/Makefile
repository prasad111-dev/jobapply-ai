.PHONY: install test lint run migrate seed clean

install:
	pip install -r requirements.txt
	playwright install chromium

test:
	pytest -v --tb=short

test-cov:
	pytest -v --cov=app --cov-report=html

lint:
	flake8 app/ --max-line-length=120
	black app/ --check
	mypy app/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	gunicorn app.main:app -c gunicorn_conf.py

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

seed:
	python -m app.core.seed

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
