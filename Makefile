PYTHON ?= python3
API_PYTHON = services/api/.venv/bin/python
.PHONY: setup dev check browser up down
setup:
	$(PYTHON) -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required; use make setup PYTHON=python3.12'"
	$(PYTHON) -m venv services/api/.venv
	$(API_PYTHON) -m pip install -r services/api/requirements-dev.txt
	$(API_PYTHON) -m pip install --no-deps -e services/api
	npm ci
dev:
	$(API_PYTHON) scripts/dev.py
check:
	cd services/api && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy && .venv/bin/python -m unittest discover -s tests
	$(API_PYTHON) scripts/contract.py --check
	npm --prefix apps/web run format:check
	npm --prefix apps/web run build
	npm run test:client
	npm run check:mobile
	npm run format:check --workspace @field-notebook/mobile
browser:
	npm --prefix apps/web test
up:
	docker compose up --build -d --wait
down:
	docker compose down

mobile:
	npm run mobile
