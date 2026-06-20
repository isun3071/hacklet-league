FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv (fast Python package manager) — pinned image, copies the static binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .
RUN uv sync --no-dev

EXPOSE 8000

# Run migrations + collect static, then serve. (makemigrations is a dev step, run
# manually once per model change — see DEPLOY.md.)
# --frozen --no-dev: use the venv baked by `uv sync --no-dev` above as-is. Without
# them, `uv run` re-syncs at boot and pulls dev tooling (ruff/mypy/faker) from PyPI
# on every fresh container — slow cold starts, and the backend can't boot if PyPI is
# down. --frozen also forbids any lockfile re-resolution at runtime (deterministic).
CMD ["sh", "-c", "uv run --frozen --no-dev python manage.py migrate --noinput && uv run --frozen --no-dev python manage.py collectstatic --noinput && uv run --frozen --no-dev gunicorn hacklet.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
