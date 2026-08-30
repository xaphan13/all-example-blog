#!/usr/bin/env sh

set -e
set -x

uvx ruff check --fix app cli
uvx ruff format app cli
uvx djlint --reformat --quiet app/templates/
