#! /bin/sh -eu

VENV="${UV_PROJECT_ENVIRONMENT:-.venv}"

# TODO: should this be a package known in the entire codebase? If so, how does setuptools help us here?
"$VENV/bin/python3" -BbbOOum server
