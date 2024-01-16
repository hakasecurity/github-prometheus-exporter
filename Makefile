VERSION = latest
IMAGE_NAME = discovery/api
CURRENT_DIR = $(shell pwd)
BUILD_TARGET ?= prod

setup:
	pip install pipx
	pipx ensurepath
	pipx install poetry

install:
	poetry install --with dev --with test

format:
	poetry run ruff format
	poetry run ruff check --fix --unsafe-fixes .

lint-formatters:
	poetry run ruff format --check
	poetry run ruff check .

lint-static-code-analysis:
	poetry run mypy .

lint: lint-formatters lint-static-code-analysis

pre-commit: format lint-static-code-analysis

build:
	docker build -t ${IMAGE_NAME} ${CACHE_FLAGS} --target ${BUILD_TARGET} -f ./Dockerfile ../..
