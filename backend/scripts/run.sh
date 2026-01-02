#! /bin/sh -eu

VENV="${UV_PROJECT_ENVIRONMENT:-.venv}"

"$VENV/bin/python3" -BbbOOum server
