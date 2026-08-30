# Imagen de producción de la app.
# Usa uv (el mismo gestor que en desarrollo) e instala exactamente
# las versiones de uv.lock, así el build es reproducible.

FROM python:3.14-slim

# Copiamos el binario de uv desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Los logs salen sin buffer (visibles al instante en docker logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /srv/diegolonio

# Dependencias primero: esta capa se cachea mientras el lock no cambie,
# así los rebuilds por cambios de código son casi instantáneos.
# --no-install-project: solo dependencias; el código se copia después.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# El venv creado por uv queda por delante en el PATH
ENV PATH="/srv/diegolonio/.venv/bin:$PATH"

# Código de la aplicación
COPY app/ app/
COPY migrations/ migrations/
COPY scripts/ scripts/
COPY projects.yaml ./

EXPOSE 8000

# --proxy-headers: confía en las cabeceras X-Forwarded-* que agrega el
# túnel de Cloudflare, para que la app vea el esquema/host reales.
# (docker-compose.prod.yml antepone las migraciones a este comando)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
