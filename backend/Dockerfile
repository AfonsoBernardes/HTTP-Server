FROM python:3.12-slim

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
VOLUME /app

# configure the project virtual environment path and set cache location
ENV UV_PROJECT_ENVIRONMENT=/app/.venv@docker
ENV UV_CACHE_DIR=.uv_cache@docker
