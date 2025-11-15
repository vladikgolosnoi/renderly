SHELL := /bin/bash

.PHONY: install lint test api test-api test-web format seed compose-up compose-down

install:
	pip install -r apps/api/requirements-dev.txt
	cd apps/web && npm install

lint:
	ruff check apps/api/app
	cd apps/web && npm run lint

test:
	make test-api
	make test-web

test-api:
	python -m pytest apps/api/tests

test-web:
	cd apps/web && npm run test

seed:
	cd apps/api && python -m app.seeds.seed_data

compose-up:
	cd infra && docker compose up -d --build

compose-down:
	cd infra && docker compose down -v
