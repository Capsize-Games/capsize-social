set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

setup:
    uv sync --extra dev

build:
    uv build

test:
    uv run pytest -q

lint:
    uv run ruff check capsize_social tests migrations

format:
    uv run ruff format capsize_social tests migrations

typecheck:
    uv run mypy capsize_social

run:
    uv run python -m capsize_social

ci: lint typecheck test build
