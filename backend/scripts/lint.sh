#! /bin/sh -eu

uvx black src/ --check
uvx isort src/ --check-only