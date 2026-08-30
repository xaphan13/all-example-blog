FROM node:22-trixie-slim AS css-builder
# Install pnpm globally using yarn
RUN yarn global add pnpm
# Use `/www/` as the working directory
WORKDIR /www/
# Then, add the dependency management files and install it
COPY ./package.json ./pnpm-lock.yaml pnpm-workspace.yaml /www/
RUN pnpm i --frozen-lockfile
# Copy asset, template, and HTML service files for CSS processing
COPY ./app/assets/ /www/app/assets/
COPY ./app/templates/ /www/app/templates/
COPY ./app/services/html.py /www/app/services/html.py
# Build the CSS files with pnpm
RUN pnpm build:css


# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS convert-images-builder
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
# Disable Python downloads, because we want to use the system interpreter
# across both images
ENV UV_PYTHON_DOWNLOADS=0
# Install the project into `/www/`
WORKDIR /www/
# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,relabel=shared \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,relabel=shared \
    uv sync --locked --no-install-project --only-group build
# Then, add the dependency management files and install it
# Installing separately from its dependencies allows optimal layer caching
COPY ./pyproject.toml ./uv.lock /www/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --only-group build


# Then, use an image without uv
FROM python:3.13-slim-trixie AS convert-images
# Use `/www/` as the working directory
WORKDIR /www/
# Copy the virtual environment from the convert-images-builder
COPY --from=convert-images-builder /www/.venv/ /www/.venv/
# Copy the required files for the image format conversion
COPY ./cli/ /www/cli/
COPY ./app/static/images/ /www/app/static/images/
# Place executables in the environment at the front of the path
ENV PATH="/www/.venv/bin:$PATH"
# Run the image format conversion script
RUN python -m cli.convert_images
RUN python -m cli.img_to_ansi


# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS runner-builder
# Install the system dependencies
RUN apt-get update && apt-get install build-essential -y
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
# Disable Python downloads, because we want to use the system interpreter
# across both images
ENV UV_PYTHON_DOWNLOADS=0
# Install the project into `/www/`
WORKDIR /www/
# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,relabel=shared \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,relabel=shared \
    uv sync --locked --no-install-project --no-dev
# Then, add the dependency management files and install it
# Installing separately from its dependencies allows optimal layer caching
COPY ./pyproject.toml ./uv.lock /www/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked  --no-dev


# Then, use a final image without uv
FROM python:3.13-slim-trixie AS runner
# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot
# Install the system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends media-types wget \
  && rm -rf /var/lib/apt/lists/*
# Use `/www/` as the working directory
WORKDIR /www/
# Copy the virtual environment from the runner-builder
COPY --from=runner-builder --chown=nonroot:nonroot /www/.venv/ /www/.venv/
# Place executables in the environment at the front of the path
ENV PATH="/www/.venv/bin:$PATH"
# Copy the application code
COPY ./app/ /www/app/
# Generate the highlight.css file
RUN mkdir -p /www/app/static/css/ && pygmentize \
    -S github-dark \
    -f html \
    -a .codehilite \
    > /www/app/static/css/highlight.css
# Copy the css styles from the css-builder
COPY --from=css-builder /www/app/static/css/ /www/app/static/css/
# Copy the images and markdown content
COPY --from=convert-images /www/app/static/images/ /www/app/static/images/
COPY --from=convert-images /www/app/ansi/ /www/app/ansi/
COPY ./content/ /www/content/
# Configure the nonroot user as the owner of the images directory
RUN chown -R nonroot:nonroot /www/app/static/images/
# Use the non-root user to run our application
USER nonroot
# Run the FastAPI application by default
EXPOSE 4000
CMD [ \
  "fastapi", "run", \
  "--port", "4000", \
  "--host", "0.0.0.0", \
  "--forwarded-allow-ips", "*", \
  "app/main.py" \
  ]
