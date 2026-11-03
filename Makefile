.PHONY: dev migrate seed-demo test lint web-build eval

dev:        ## Levanta todo con Docker Compose
	docker compose up --build

migrate:    ## Aplica las migraciones
	cd backend && alembic upgrade head

seed-demo:  ## Roles y usuarios de DATOS DEMO (requiere ARRIERA_DEMO_CLAVE)
	cd backend && python -m arriera.seed --demo

test:       ## Pruebas del backend contra PostgreSQL (DATABASE_URL de pruebas en tests/conftest.py)
	cd backend && python -m pytest -q

lint:       ## Linter, formato y tipos
	cd backend && ruff check arriera tests alembic && ruff format --check arriera tests alembic
	cd web && npx tsc --noEmit

web-build:  ## Compila la web
	cd web && npm run build

eval:       ## Evalúa la IA con el set de referencia DEMO (usa la IA configurada y cuenta contra el presupuesto)
	cd backend && python -m arriera.eval --docs 12
