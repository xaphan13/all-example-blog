#!/usr/bin/env sh

set -e
set -x

uvx ty check app cli
uvx ruff check app cli
uvx ruff format --check app cli
uvx djlint --check app/templates/
uvx djlint --lint app/templates/
