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
CMD ["sh", "-c", "uv run python manage.py migrate --noinput && uv run python manage.py collectstatic --noinput && uv run gunicorn hacklet.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
