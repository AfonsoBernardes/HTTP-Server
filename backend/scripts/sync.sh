#! /bin/sh -eu

VENV="${UV_PROJECT_ENVIRONMENT:-.venv}"

uv sync --cache-dir "${UV_CACHE_DIR:-.uv_cache}"
touch --no-create "$VENV"
