.DEFAULT_GOAL := stage

# User-configurable
PORT ?= 4000
CONTAINER_TOOL ?= podman-compose

# Base paths
VENV := .venv/bin
PYTHON := $(VENV)/python3
IMG_DIR := app/static/images

# Outputs
STYLES_CSS := app/static/css/styles.css
HIGHLIGHT_CSS := app/static/css/highlight.css

# State (stamps)
DEPS_STAMP := .venv/.deps-installed
NODE_STAMP := node_modules/.deps-installed
PRECOMMIT_STAMP := .git/hooks/pre-commit
OPTIMIZE_STAMP := .cache/images-optimize.stamp
ANSI_STAMP := .cache/images-ansi.stamp

# Derived
IMGS := $(shell find $(IMG_DIR) -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \))

.PHONY: prod
prod:
	$(CONTAINER_TOOL) -f ./compose.prod.yaml up -d --build

.PHONY: prod-stop
prod-stop:
	$(CONTAINER_TOOL) -f ./compose.prod.yaml down

.PHONY: stage
stage:
	$(CONTAINER_TOOL) -f ./compose.stage.yaml up -d --build

.PHONY: stage-stop
stage-stop:
	$(CONTAINER_TOOL) -f ./compose.stage.yaml down

.PHONY: dev
dev:
	$(CONTAINER_TOOL) -f ./compose.dev.yaml up -d --build

.PHONY: dev-stop
dev-stop:
	$(CONTAINER_TOOL) -f ./compose.dev.yaml down

$(DEPS_STAMP): pyproject.toml uv.lock
	uv sync --all-groups
	@mkdir -p .venv
	@touch $@

$(NODE_STAMP): package.json pnpm-lock.yaml
	pnpm install --frozen-lockfile
	@mkdir -p node_modules
	@touch $@

$(PRECOMMIT_STAMP): .pre-commit-config.yaml
	uvx prek install
	@touch $@

$(HIGHLIGHT_CSS): $(DEPS_STAMP)
	$(VENV)/pygmentize \
		-S github-dark \
		-f html \
		-a .codehilite \
		> $(HIGHLIGHT_CSS)

$(STYLES_CSS): $(NODE_STAMP)
	pnpm run build:css

$(OPTIMIZE_STAMP): $(DEPS_STAMP) $(IMGS)
	@mkdir -p .cache
	$(PYTHON) -m cli.convert_images
	@touch $@

$(ANSI_STAMP): $(DEPS_STAMP) $(IMGS)
	@mkdir -p .cache
	$(PYTHON) -m cli.img_to_ansi
	@touch $@

.PHONY: images-optimize
images-optimize: $(OPTIMIZE_STAMP)

.PHONY: images-ansi
images-ansi: $(ANSI_STAMP)

.PHONY: local-styles
local-styles: $(NODE_STAMP)
	pnpm run dev:css

.PHONY: local-dev
local-dev: $(DEPS_STAMP) $(STYLES_CSS) $(HIGHLIGHT_CSS) $(ANSI_STAMP) $(OPTIMIZE_STAMP)
	$(PYTHON) -m fastapi dev --port $(PORT) app/main.py

.PHONY: local-prod
local-prod: $(DEPS_STAMP) $(STYLES_CSS) $(HIGHLIGHT_CSS) $(ANSI_STAMP) $(OPTIMIZE_STAMP)
	$(PYTHON) -m fastapi run --port $(PORT) app/main.py

.PHONY: format
format: $(DEPS_STAMP)
	sh ./scripts/format.sh

.PHONY: lint
lint: $(DEPS_STAMP)
	sh ./scripts/lint.sh

.PHONY: check
check: $(DEPS_STAMP)
	uvx prek run --all-files

.PHONY: setup
setup: $(DEPS_STAMP) $(NODE_STAMP) $(PRECOMMIT_STAMP)
	@echo ">> Dev environment ready."

.PHONY: clean
clean:
	find app/ -type d -name "ansi" -prune -print -exec rm -rf -- {} +
	find app/static/ -type d -name "author" -prune -print -exec rm -rf -- {} +
	find . -type d \( \
		-name "__pycache__" -o \
		-name ".cache" \
	\) -prune -print -exec rm -rf -- {} +
	find app/static/ -type f \( \
		-name "*.css" -o \
		-name "*.webp" -o \
		-name "*.avif" \
	\) -print -delete

.PHONY: fclean
fclean: clean
	find . -type d \( \
		-name ".ruff_cache" -o \
	  -name ".venv" -o \
		-name "node_modules" \
	\) -prune -print -exec rm -rf -- {} +

.PHONY: re
re: fclean stage
